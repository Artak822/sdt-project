import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service.config import settings
from services.user_service.crud import (
    get_user, get_or_create_user,
    get_profile_by_user, get_profile_by_id,
    create_profile, update_profile, delete_profile, get_feed_profiles,
)
from services.user_service.database import create_tables, get_session
from services.user_service.rabbitmq import start_consuming, stop_consuming
from services.user_service.schemas import (
    UserCreate, UserResponse,
    ProfileCreate, ProfileUpdate, ProfileResponse,
)

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await create_tables()
    consume_task = asyncio.create_task(start_consuming())
    logger.info("User service started")
    yield
    consume_task.cancel()
    await stop_consuming()
    logger.info("User service stopped")


app = FastAPI(title="User Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, session: AsyncSession = Depends(get_session)) -> UserResponse:
    user = await get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: UserCreate, session: AsyncSession = Depends(get_session)
) -> UserResponse:
    user, created = await get_or_create_user(session, body.user_id, body.username)
    if not created:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=UserResponse.model_validate(user).model_dump(mode="json"),
            status_code=status.HTTP_200_OK,
        )
    return user


@app.get("/profiles/user/{user_id}", response_model=ProfileResponse)
async def read_profile_by_user(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> ProfileResponse:
    profile = await get_profile_by_user(session, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@app.get("/profiles/{profile_id}", response_model=ProfileResponse)
async def read_profile(
    profile_id: UUID, session: AsyncSession = Depends(get_session)
) -> ProfileResponse:
    profile = await get_profile_by_id(session, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@app.post("/profiles/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    body: ProfileCreate, session: AsyncSession = Depends(get_session)
) -> ProfileResponse:
    existing = await get_profile_by_user(session, body.user_id)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Profile already exists")
    profile = await create_profile(
        session,
        user_id=body.user_id,
        name=body.name,
        age=body.age,
        gender=body.gender,
        looking_for=body.looking_for,
        bio=body.bio,
        city=body.city,
        age_range_min=body.age_range_min,
        age_range_max=body.age_range_max,
        photo_id=body.photo_id,
    )
    return profile


@app.patch("/profiles/user/{user_id}", response_model=ProfileResponse)
async def update_user_profile(
    user_id: int, body: ProfileUpdate, session: AsyncSession = Depends(get_session)
) -> ProfileResponse:
    profile = await get_profile_by_user(session, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    profile = await update_profile(session, profile, **body.model_dump(exclude_none=True))
    return profile


@app.delete("/profiles/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    profile = await get_profile_by_user(session, user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    await delete_profile(session, profile)


@app.get("/profiles/feed/{user_id}", response_model=List[ProfileResponse])
async def get_profile_feed(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    excluded: str = Query(default=""),
    session: AsyncSession = Depends(get_session),
) -> List[ProfileResponse]:
    excluded_ids = [int(x) for x in excluded.split(",") if x.strip().isdigit()]
    profiles = await get_feed_profiles(session, user_id, limit=limit, excluded_ids=excluded_ids)
    return profiles
