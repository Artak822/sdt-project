import json
import logging
from datetime import datetime, timezone
from typing import Optional

import aio_pika

from bot.config import settings

logger = logging.getLogger(__name__)

_connection: Optional[aio_pika.RobustConnection] = None
_channel: Optional[aio_pika.Channel] = None


async def connect_rabbitmq() -> None:
    global _connection, _channel
    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    _channel = await _connection.channel()
    await _channel.declare_exchange(
        "dating.exchange", aio_pika.ExchangeType.DIRECT, durable=True
    )
    logger.info("RabbitMQ connected")


async def close_rabbitmq() -> None:
    if _connection and not _connection.is_closed:
        await _connection.close()
    logger.info("RabbitMQ connection closed")


async def _publish(routing_key: str, payload: dict) -> None:
    if _channel is None:
        logger.error("RabbitMQ channel is not initialized")
        return
    exchange = await _channel.get_exchange("dating.exchange")
    message = aio_pika.Message(
        body=json.dumps(payload).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)


async def publish_user_register(user_id: int, username: Optional[str]) -> None:
    payload = {
        "event": "user.register",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"user_id": user_id, "username": username},
    }
    await _publish("user.register", payload)
    logger.info("Published user.register for user_id=%d", user_id)
