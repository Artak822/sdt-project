import uuid
import logging
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from services.match_service.models import Like, Match

logger = logging.getLogger(__name__)


async def get_like(session: AsyncSession, from_user_id: int, to_user_id: int) -> Optional[Like]:
    result = await session.execute(
        select(Like).where(and_(Like.from_user_id == from_user_id, Like.to_user_id == to_user_id))
    )
    return result.scalar_one_or_none()


async def create_like(
    session: AsyncSession, from_user_id: int, to_user_id: int, to_profile_id: UUID
) -> Like:
    like = Like(
        id=uuid.uuid4(),
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        to_profile_id=to_profile_id,
    )
    session.add(like)
    await session.commit()
    await session.refresh(like)
    return like


async def check_mutual_like(session: AsyncSession, from_user_id: int, to_user_id: int) -> bool:
    reverse = await get_like(session, to_user_id, from_user_id)
    return reverse is not None


async def get_match(session: AsyncSession, user1_id: int, user2_id: int) -> Optional[Match]:
    smaller, larger = sorted([user1_id, user2_id])
    result = await session.execute(
        select(Match).where(and_(Match.user1_id == smaller, Match.user2_id == larger))
    )
    return result.scalar_one_or_none()


async def create_match(session: AsyncSession, user1_id: int, user2_id: int) -> Match:
    smaller, larger = sorted([user1_id, user2_id])
    match = Match(id=uuid.uuid4(), user1_id=smaller, user2_id=larger)
    session.add(match)
    for a, b in [(user1_id, user2_id), (user2_id, user1_id)]:
        like = await get_like(session, a, b)
        if like:
            like.is_mutual = True
    await session.commit()
    await session.refresh(match)
    logger.info("Match created: user1=%d, user2=%d", user1_id, user2_id)
    return match


async def get_user_matches(session: AsyncSession, user_id: int) -> List[Match]:
    result = await session.execute(
        select(Match).where((Match.user1_id == user_id) | (Match.user2_id == user_id))
    )
    return list(result.scalars().all())
