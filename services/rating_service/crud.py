import uuid
import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.rating_service.models import Rating

logger = logging.getLogger(__name__)


async def get_rating(session: AsyncSession, profile_id: UUID) -> Optional[Rating]:
    result = await session.execute(select(Rating).where(Rating.profile_id == profile_id))
    return result.scalar_one_or_none()


async def create_or_update_rating(
    session: AsyncSession,
    profile_id: UUID,
    primary_score: Decimal,
    behavioral_score: Decimal,
    combined_score: Decimal,
) -> Rating:
    rating = await get_rating(session, profile_id)
    if not rating:
        rating = Rating(
            id=uuid.uuid4(),
            profile_id=profile_id,
            primary_score=primary_score,
            behavioral_score=behavioral_score,
            combined_score=combined_score,
        )
        session.add(rating)
    else:
        rating.primary_score = primary_score
        rating.behavioral_score = behavioral_score
        rating.combined_score = combined_score
    await session.commit()
    await session.refresh(rating)
    logger.info("Rating updated: profile_id=%s, combined=%.2f", profile_id, combined_score)
    return rating
