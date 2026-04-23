from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.match_service.crud import create_like, check_mutual_like, get_match, create_match, get_like
from services.match_service.models import Like, Match


async def process_like(
    session: AsyncSession,
    from_user_id: int,
    to_user_id: int,
    to_profile_id: UUID,
) -> tuple[Like, bool, Optional[Match]]:
    existing = await get_like(session, from_user_id, to_user_id)
    if existing:
        match = await get_match(session, from_user_id, to_user_id)
        return existing, match is not None, match

    like = await create_like(session, from_user_id, to_user_id, to_profile_id)
    is_mutual = await check_mutual_like(session, from_user_id, to_user_id)

    match = None
    if is_mutual:
        existing_match = await get_match(session, from_user_id, to_user_id)
        match = existing_match or await create_match(session, from_user_id, to_user_id)

    return like, is_mutual, match
