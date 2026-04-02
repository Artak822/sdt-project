import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service.models import User

logger = logging.getLogger(__name__)


async def get_user(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession, user_id: int, username: Optional[str]
) -> User:
    user = User(id=user_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("User created: id=%d, username=%s", user_id, username)
    return user


async def get_or_create_user(
    session: AsyncSession, user_id: int, username: Optional[str]
) -> tuple[User, bool]:
    """Возвращает (user, created). created=True если пользователь новый."""
    user = await get_user(session, user_id)
    if user:
        return user, False
    user = await create_user(session, user_id, username)
    return user, True
