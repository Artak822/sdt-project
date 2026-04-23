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


async def publish_profile_complete(
    profile_id: str,
    user_id: int,
    name: str,
    age: int,
    gender: str,
    bio: Optional[str],
    city: Optional[str],
    looking_for: str,
    photo_id: Optional[str],
) -> None:
    payload = {
        "event": "user.profile.complete",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "profile_id": profile_id,
            "user_id": user_id,
            "name": name,
            "age": age,
            "gender": gender,
            "bio": bio,
            "city": city,
            "looking_for": looking_for,
            "photo_id": photo_id,
        },
    }
    await _publish("user.profile.complete", payload)
    logger.info("Published user.profile.complete for user_id=%d", user_id)


async def publish_user_like(from_user_id: int, to_user_id: int, to_profile_id: str) -> None:
    payload = {
        "event": "user.like",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "to_profile_id": to_profile_id,
        },
    }
    await _publish("user.like", payload)
    logger.info("Published user.like from_user_id=%d to_user_id=%d", from_user_id, to_user_id)
