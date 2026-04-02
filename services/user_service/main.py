import asyncio
import logging

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service.config import settings
from services.user_service.crud import get_user, get_or_create_user
from services.user_service.database import create_tables, get_session
from services.user_service.rabbitmq import start_consuming, stop_consuming
from services.user_service.schemas import UserCreate, UserResponse

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await create_tables()
    # Запускаем consumer в фоне
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
async def read_user(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> UserResponse:
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
        # Пользователь уже существует — возвращаем 200
        from fastapi.responses import JSONResponse
        from services.user_service.schemas import UserResponse as UR
        return JSONResponse(
            content=UR.model_validate(user).model_dump(mode="json"),
            status_code=status.HTTP_200_OK,
        )
    return user
