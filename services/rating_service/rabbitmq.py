import json
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from services.rating_service.config import settings
from services.rating_service.crud import create_or_update_rating, get_rating
from services.rating_service.database import AsyncSessionFactory
from services.rating_service.algorithms import calc_primary_score, calc_combined_score

logger = logging.getLogger(__name__)
_connection: Optional[aio_pika.RobustConnection] = None


async def handle_profile_complete(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            body = json.loads(message.body)
            data = body["data"]
            profile_id = UUID(data["profile_id"])
            primary = calc_primary_score(
                has_name=bool(data.get("name")),
                has_age=bool(data.get("age")),
                has_gender=bool(data.get("gender")),
                has_bio=bool(data.get("bio")),
                has_city=bool(data.get("city")),
                has_looking_for=bool(data.get("looking_for")),
                has_photo=bool(data.get("photo_id")),
            )
            combined = calc_combined_score(primary, Decimal("0"))
            async with AsyncSessionFactory() as session:
                await create_or_update_rating(session, profile_id, primary, Decimal("0"), combined)
        except Exception as exc:
            logger.error("Error handling profile.complete: %s", exc)


async def handle_user_like(message: AbstractIncomingMessage) -> None:
    async with message.process():
        try:
            body = json.loads(message.body)
            data = body["data"]
            to_profile_id = UUID(data["to_profile_id"])
            async with AsyncSessionFactory() as session:
                rating = await get_rating(session, to_profile_id)
                if rating:
                    new_behavioral = min(Decimal("100"), rating.behavioral_score + Decimal("2"))
                    new_combined = calc_combined_score(rating.primary_score, new_behavioral)
                    await create_or_update_rating(
                        session, to_profile_id,
                        rating.primary_score, new_behavioral, new_combined,
                    )
        except Exception as exc:
            logger.error("Error handling user.like for rating: %s", exc)


async def start_consuming() -> None:
    global _connection
    _connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        "dating.exchange", aio_pika.ExchangeType.DIRECT, durable=True
    )

    profile_queue = await channel.declare_queue("profile_complete_queue", durable=True)
    await profile_queue.bind(exchange, routing_key="user.profile.complete")
    await profile_queue.consume(handle_profile_complete)

    like_queue = await channel.declare_queue("likes_rating_queue", durable=True)
    await like_queue.bind(exchange, routing_key="user.like")
    await like_queue.consume(handle_user_like)

    logger.info("Rating service started consuming")


async def stop_consuming() -> None:
    if _connection and not _connection.is_closed:
        await _connection.close()
