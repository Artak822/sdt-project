import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.rating_service.config import settings
from services.rating_service.crud import get_rating
from services.rating_service.database import create_tables, get_session
from services.rating_service.rabbitmq import start_consuming, stop_consuming
from services.rating_service.schemas import RatingResponse

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await create_tables()
    consume_task = asyncio.create_task(start_consuming())
    logger.info("Rating service started")
    yield
    consume_task.cancel()
    await stop_consuming()
    logger.info("Rating service stopped")


app = FastAPI(title="Rating Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ratings/{profile_id}", response_model=RatingResponse)
async def read_rating(
    profile_id: UUID, session: AsyncSession = Depends(get_session)
) -> RatingResponse:
    rating = await get_rating(session, profile_id)
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rating not found")
    return rating
