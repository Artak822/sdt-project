import json
import logging
from typing import Optional

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from services.user_service.config import settings
from services.user_service.crud import get_or_create_user
from services.user_service.database import AsyncSessionFactory

logger = logging.getLogger(__name__)

_connection: Optional[aio_pika.RobustConnection] = None


async def handle_user_register(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            payload = json.loads(message.body)
            data = payload["data"]
            user_id: int = data["user_id"]
            username: Optional[str] = data.get("username")

            async with AsyncSessionFactory() as session:
                user, created = await get_or_create_user(session, user_id, username)

            if created:
                logger.info("New user registered via MQ: id=%d", user_id)
            else:
                logger.debug("User already exists: id=%d", user_id)

        except Exception as exc:
            logger.error("Failed to process user.register message: %s", exc)


async def start_consuming() -> None:
    global _connection
    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        "dating.exchange", aio_pika.ExchangeType.DIRECT, durable=True
    )
    queue = await channel.declare_queue("register_queue", durable=True)
    await queue.bind(exchange, routing_key="user.register")

    await queue.consume(handle_user_register)
    logger.info("Started consuming register_queue")


async def stop_consuming() -> None:
    if _connection and not _connection.is_closed:
        await _connection.close()
