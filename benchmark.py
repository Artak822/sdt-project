#!/usr/bin/env python3
"""
RabbitMQ vs Redis — Message Broker Benchmark
Measures: throughput, avg/p95/max latency, message loss.

Usage:
  python benchmark.py               # run all scenarios
  python benchmark.py --rabbit-only
  python benchmark.py --redis-only
"""

import threading
import time
import json
import statistics
import sys
import os
import datetime
from dataclasses import dataclass, field
from typing import List, Callable

import pika
import redis as redis_lib

# ── connection settings ────────────────────────────────────────────────────────
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")
RABBIT_PORT = int(os.getenv("RABBIT_PORT", "5672"))
REDIS_HOST  = os.getenv("REDIS_HOST",  "localhost")
REDIS_PORT  = int(os.getenv("REDIS_PORT",  "6379"))

QUEUE_NAME   = "bench"
STREAM_KEY   = "bench_s"
STREAM_GROUP = "bench_g"
STREAM_CONS  = "c1"

DRAIN_SEC    = 5   # seconds to drain remaining messages after producer stops
COOLDOWN_SEC = 3   # cooldown between scenarios


# ── result dataclass ───────────────────────────────────────────────────────────

@dataclass
class Result:
    broker: str
    size: int
    rate: int
    dur: int
    sent: int = 0
    recv: int = 0
    errs: int = 0
    lats: List[float] = field(default_factory=list)

    @property
    def lost(self) -> int:
        return max(0, self.sent - self.recv)

    @property
    def tput(self) -> float:
        return self.recv / self.dur if self.dur else 0

    @property
    def avg_lat(self) -> float:
        return statistics.mean(self.lats) if self.lats else 0.0

    @property
    def p95_lat(self) -> float:
        if not self.lats:
            return 0.0
        s = sorted(self.lats)
        return s[max(0, int(len(s) * 0.95) - 1)]

    @property
    def max_lat(self) -> float:
        return max(self.lats) if self.lats else 0.0

    def row(self) -> dict:
        return {
            "broker":   self.broker,
            "size_b":   self.size,
            "rate":     self.rate,
            "dur":      self.dur,
            "sent":     self.sent,
            "recv":     self.recv,
            "lost":     self.lost,
            "tput":     round(self.tput,    1),
            "avg_ms":   round(self.avg_lat, 2),
            "p95_ms":   round(self.p95_lat, 2),
            "max_ms":   round(self.max_lat, 2),
            "errs":     self.errs,
        }


# ── helpers ────────────────────────────────────────────────────────────────────

def fmt_sz(n: int) -> str:
    if n < 1024:       return f"{n}B"
    if n < 1048576:    return f"{n // 1024}KB"
    return f"{n // 1048576}MB"


def _producer_loop(send_fn: Callable, rate: int, dur: int,
                   sent_box: list, err_box: list, done_event: threading.Event):
    """Generic rate-limited producer loop."""
    interval = 1.0 / rate
    next_t   = time.time()
    end_t    = next_t + dur

    while time.time() < end_t:
        now = time.time()
        if now >= next_t:
            try:
                send_fn()
                sent_box[0] += 1
            except Exception:
                err_box[0] += 1
            next_t += interval
        else:
            gap = next_t - now - 0.0003
            if gap > 0:
                time.sleep(gap)

    done_event.set()


# ── RabbitMQ ───────────────────────────────────────────────────────────────────

def _rmq_conn() -> pika.BlockingConnection:
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBIT_HOST, port=RABBIT_PORT,
        credentials=pika.PlainCredentials("guest", "guest"),
        heartbeat=600,
        blocked_connection_timeout=300,
    ))


def _rmq_reset():
    conn = _rmq_conn()
    ch = conn.channel()
    ch.queue_delete(queue=QUEUE_NAME)
    ch.queue_declare(queue=QUEUE_NAME, durable=False)
    conn.close()


def bench_rabbit(size: int, rate: int, dur: int) -> Result:
    r        = Result("RabbitMQ", size, rate, dur)
    payload  = "x" * size       # string payload of exact size
    lock     = threading.Lock()
    prod_done = threading.Event()
    sent_box = [0]
    err_box  = [0]
    lats_shared: List[float] = []

    _rmq_reset()

    # ── producer ──
    def producer():
        conn = _rmq_conn()
        ch   = conn.channel()
        ch.confirm_delivery()  # publisher confirms → честный round-trip как у Redis

        def _send():
            body = json.dumps({"ts": time.time(), "p": payload}).encode()
            ch.basic_publish(
                exchange="", routing_key=QUEUE_NAME, body=body,
                properties=pika.BasicProperties(delivery_mode=1),
            )

        _producer_loop(_send, rate, dur, sent_box, err_box, prod_done)
        conn.close()

    # ── consumer ──
    def consumer():
        conn = _rmq_conn()
        ch   = conn.channel()
        ch.basic_qos(prefetch_count=500)
        lats_local: List[float] = []

        def on_msg(ch, method, _props, body):
            recv_t = time.time()
            msg    = json.loads(body)
            lats_local.append((recv_t - msg["ts"]) * 1000)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        ch.basic_consume(QUEUE_NAME, on_message_callback=on_msg)
        drain_until = None

        while True:
            conn.process_data_events(time_limit=0.1)
            if prod_done.is_set() and drain_until is None:
                drain_until = time.time() + DRAIN_SEC
            if drain_until and time.time() >= drain_until:
                break

        conn.close()
        with lock:
            lats_shared.extend(lats_local)

    ct = threading.Thread(target=consumer, daemon=True)
    pt = threading.Thread(target=producer, daemon=True)
    ct.start()
    pt.start()
    pt.join()
    ct.join(timeout=DRAIN_SEC + 5)

    r.sent = sent_box[0]
    r.errs = err_box[0]
    r.recv = len(lats_shared)
    r.lats = lats_shared
    return r


# ── Redis ──────────────────────────────────────────────────────────────────────

def _red_conn() -> redis_lib.Redis:
    return redis_lib.Redis(
        host=REDIS_HOST, port=REDIS_PORT,
        decode_responses=False, socket_connect_timeout=5,
    )


def _red_reset():
    rc = _red_conn()
    rc.delete(STREAM_KEY)
    rc.xgroup_create(STREAM_KEY, STREAM_GROUP, id="$", mkstream=True)
    rc.close()


def bench_redis(size: int, rate: int, dur: int) -> Result:
    r         = Result("Redis", size, rate, dur)
    payload   = b"x" * size
    lock      = threading.Lock()
    prod_done = threading.Event()
    sent_box  = [0]
    err_box   = [0]
    lats_shared: List[float] = []

    # Ограничиваем стрим ~300 MB чтобы не упасть в OOM
    stream_maxlen = max(500, (300 * 1024 * 1024) // max(size, 1))
    stream_maxlen = min(stream_maxlen, 50_000)

    _red_reset()

    # ── producer ──
    def producer():
        rc = _red_conn()

        def _send():
            rc.xadd(STREAM_KEY, {"ts": str(time.time()), "p": payload},
                    maxlen=stream_maxlen, approximate=True)

        _producer_loop(_send, rate, dur, sent_box, err_box, prod_done)
        rc.close()

    # ── consumer ──
    def consumer():
        rc = _red_conn()
        lats_local: List[float] = []
        drain_until = None

        while True:
            try:
                msgs = rc.xreadgroup(
                    STREAM_GROUP, STREAM_CONS,
                    {STREAM_KEY: ">"},
                    count=500, block=50,
                )
                if msgs:
                    recv_t = time.time()
                    ids = []
                    for _, entries in msgs:
                        for mid, fields in entries:
                            ts = float(fields[b"ts"])
                            lats_local.append((recv_t - ts) * 1000)
                            ids.append(mid)
                    if ids:
                        rc.xack(STREAM_KEY, STREAM_GROUP, *ids)
            except Exception:
                pass

            if prod_done.is_set() and drain_until is None:
                drain_until = time.time() + DRAIN_SEC
            if drain_until and time.time() >= drain_until:
                break

        rc.close()
        with lock:
            lats_shared.extend(lats_local)

    ct = threading.Thread(target=consumer, daemon=True)
    pt = threading.Thread(target=producer, daemon=True)
    ct.start()
    pt.start()
    pt.join()
    ct.join(timeout=DRAIN_SEC + 5)

    r.sent = sent_box[0]
    r.errs = err_box[0]
    r.recv = len(lats_shared)
    r.lats = lats_shared
    return r


# ── wait for brokers ───────────────────────────────────────────────────────────

def wait_rabbit(timeout=60):
    print("  Waiting for RabbitMQ...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            c = _rmq_conn(); c.close()
            print(" ready.")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(2)
    raise RuntimeError("RabbitMQ did not become ready in time")


def wait_redis(timeout=60):
    print("  Waiting for Redis...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            rc = _red_conn()
            rc.ping(); rc.close()
            print(" ready.")
            return
        except Exception:
            print(".", end="", flush=True)
            time.sleep(2)
    raise RuntimeError("Redis did not become ready in time")


# ── scenarios ──────────────────────────────────────────────────────────────────

# (size_bytes, rate_msg/s, duration_sec)
SIZE_SWEEP = [
    (128,     1_000, 30),
    (1_024,   1_000, 30),
    (10_240,  1_000, 30),
    (102_400,   500, 30),
]
RATE_SWEEP = [
    (128,  1_000, 30),
    (128,  5_000, 30),
    (128, 10_000, 30),
    (128, 20_000, 20),
    (128, 50_000, 15),
]

# deduplicated ordered union
_seen = set()
SCENARIOS = []
for s in SIZE_SWEEP + RATE_SWEEP:
    if s not in _seen:
        _seen.add(s)
        SCENARIOS.append(s)


# ── main ───────────────────────────────────────────────────────────────────────

HDR = (f"  {'broker':8}  {'size':6}  {'rate':>7}  {'dur':>4}  "
       f"{'sent':>7}  {'recv':>7}  {'lost':>5}  "
       f"{'tput msg/s':>10}  {'avg ms':>7}  {'p95 ms':>8}  {'max ms':>8}")
SEP = "  " + "-" * 98


def print_row(d: dict):
    print(f"  {d['broker']:8}  {fmt_sz(d['size_b']):6}  {d['rate']:7d}  {d['dur']:4d}s  "
          f"{d['sent']:7d}  {d['recv']:7d}  {d['lost']:5d}  "
          f"{d['tput']:10.1f}  {d['avg_ms']:7.2f}  {d['p95_ms']:8.2f}  {d['max_ms']:8.2f}")


def run_all(run_rabbit=True, run_redis=True):
    os.makedirs("results", exist_ok=True)
    ts_str   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    all_rows = []

    print()
    print("=" * 100)
    print("  RabbitMQ vs Redis — Broker Benchmark")
    print(f"  {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 100)
    print()

    wait_rabbit()
    wait_redis()

    print()
    print(HDR)
    print(SEP)

    group_label = ""
    for size, rate, dur in SCENARIOS:
        if size == 128 and rate == 5_000 and group_label != "RATE_SWEEP":
            group_label = "RATE_SWEEP"
            print(f"\n  ── Rate sweep (128B payload) ──")
        elif size != 128 and group_label != "SIZE_SWEEP":
            group_label = "SIZE_SWEEP"
            print(f"\n  ── Size sweep (1 000 msg/s) ──")

        benches: List[tuple] = []
        if run_rabbit: benches.append((bench_rabbit, "RabbitMQ"))
        if run_redis:  benches.append((bench_redis,  "Redis   "))

        for bench_fn, name in benches:
            print(f"  {name}  {fmt_sz(size):6}  {rate:7d}  {dur:4d}s  running...",
                  end="\r", flush=True)
            r = bench_fn(size, rate, dur)
            d = r.row()
            all_rows.append(d)
            print_row(d)
            time.sleep(COOLDOWN_SEC)

    print(SEP)
    out = f"results/bench_{ts_str}.json"
    with open(out, "w") as f:
        json.dump(all_rows, f, indent=2)
    print(f"\n  Saved → {out}\n")
    return out, all_rows


if __name__ == "__main__":
    run_rabbit = "--redis-only"  not in sys.argv
    run_redis  = "--rabbit-only" not in sys.argv
    run_all(run_rabbit=run_rabbit, run_redis=run_redis)
