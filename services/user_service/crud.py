import logging
import uuid
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, Table, Column, MetaData, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service.models import User, Profile, GenderEnum, LookingForEnum

_ratings = Table(
    "ratings",
    MetaData(),
    Column("profile_id", PGUUID(as_uuid=True)),
    Column("combined_score", Numeric(5, 2)),
)

logger = logging.getLogger(__name__)


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, user_id: int, username: Optional[str]) -> User:
    user = User(id=user_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("User created: id=%d, username=%s", user_id, username)
    return user


async def get_or_create_user(
    session: AsyncSession, user_id: int, username: Optional[str]
) -> tuple[User, bool]:
    user = await get_user(session, user_id)
    if user:
        return user, False
    user = await create_user(session, user_id, username)
    return user, True


async def get_profile_by_user(session: AsyncSession, user_id: int) -> Optional[Profile]:
    result = await session.execute(select(Profile).where(Profile.user_id == user_id))
    return result.scalar_one_or_none()


async def get_profile_by_id(session: AsyncSession, profile_id: UUID) -> Optional[Profile]:
    result = await session.execute(select(Profile).where(Profile.id == profile_id))
    return result.scalar_one_or_none()


async def create_profile(
    session: AsyncSession,
    user_id: int,
    name: str,
    age: int,
    gender: str,
    looking_for: str,
    bio: Optional[str] = None,
    city: Optional[str] = None,
    age_range_min: int = 18,
    age_range_max: int = 60,
    photo_id: Optional[str] = None,
) -> Profile:
    profile = Profile(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        age=age,
        gender=GenderEnum(gender),
        looking_for=LookingForEnum(looking_for),
        bio=bio,
        city=city,
        age_range_min=age_range_min,
        age_range_max=age_range_max,
        photo_id=photo_id,
        is_complete=True,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    logger.info("Profile created: user_id=%d", user_id)
    return profile


REQUIRED_PROFILE_FIELDS = {"name", "age", "gender", "looking_for"}


async def update_profile(session: AsyncSession, profile: Profile, **kwargs) -> Profile:
    for key, value in kwargs.items():
        if value is None and key in REQUIRED_PROFILE_FIELDS:
            continue
        if key == "gender" and value is not None:
            value = GenderEnum(value)
        elif key == "looking_for" and value is not None:
            value = LookingForEnum(value)
        setattr(profile, key, value)
    await session.commit()
    await session.refresh(profile)
    return profile


async def delete_profile(session: AsyncSession, profile: Profile) -> None:
    await session.delete(profile)
    await session.commit()


async def get_feed_profiles(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
    excluded_ids: Optional[List[int]] = None,
) -> List[Profile]:
    query = (
        select(Profile)
        .outerjoin(_ratings, _ratings.c.profile_id == Profile.id)
        .where(and_(Profile.user_id != user_id, Profile.is_complete.is_(True)))
        .order_by(_ratings.c.combined_score.desc().nullslast())
        .limit(limit)
    )
    if excluded_ids:
        query = query.where(Profile.user_id.not_in(excluded_ids))
    result = await session.execute(query)
    return list(result.scalars().all())
