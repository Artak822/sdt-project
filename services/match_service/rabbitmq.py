import json
import logging
from datetime import datetime, timezone
from typing import Optional

import aio_pika

from services.match_service.config import settings

logger = logging.getLogger(__name__)
_connection: Optional[aio_pika.RobustConnection] = None
_channel: Optional[aio_pika.Channel] = None


async def connect_rabbitmq() -> None:
    global _connection, _channel
    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    _channel = await _connection.channel()
    await _channel.declare_exchange("dating.exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    logger.info("Match service RabbitMQ connected")


async def close_rabbitmq() -> None:
    if _connection and not _connection.is_closed:
        await _connection.close()


async def publish_match(user1_id: int, user2_id: int, match_id: str) -> None:
    if not _channel:
        return
    exchange = await _channel.get_exchange("dating.exchange")
    payload = {
        "event": "user.match",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"user1_id": user1_id, "user2_id": user2_id, "match_id": match_id},
    }
    await exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        ),
        routing_key="user.match",
    )
