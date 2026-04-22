#!/usr/bin/env bash
set -e

echo "========================================"
echo "  Broker Benchmark — Setup & Run"
echo "========================================"

# ── 1. Install Python deps ─────────────────────────────────────────────────────
echo
echo "[1/4] Installing Python dependencies..."
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

# ── 2. Start brokers via Docker Compose ───────────────────────────────────────
echo
echo "[2/4] Starting RabbitMQ and Redis via Docker Compose..."
docker compose up -d

echo "      Waiting for health checks..."
for i in $(seq 1 30); do
    rmq_ok=$(docker inspect --format='{{.State.Health.Status}}' bench_rabbit 2>/dev/null || echo "missing")
    red_ok=$(docker inspect --format='{{.State.Health.Status}}' bench_redis  2>/dev/null || echo "missing")
    if [[ "$rmq_ok" == "healthy" && "$red_ok" == "healthy" ]]; then
        echo "      Both brokers healthy."
        break
    fi
    printf "      RabbitMQ=%s  Redis=%s  (attempt %d/30)\r" "$rmq_ok" "$red_ok" "$i"
    sleep 3
done
echo

# ── 3. Run benchmark ──────────────────────────────────────────────────────────
echo "[3/4] Running benchmark..."
.venv/bin/python benchmark.py "$@"

# ── 4. Generate report ────────────────────────────────────────────────────────
echo
echo "[4/4] Generating Markdown report..."
.venv/bin/python generate_report.py

echo
echo "Done. Results are in the results/ directory."
echo "========================================"
