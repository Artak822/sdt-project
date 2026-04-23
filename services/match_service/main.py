import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, List

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from services.match_service.config import settings
from services.match_service.crud import get_user_matches
from services.match_service.database import create_tables, get_session
from services.match_service.logic import process_like
from services.match_service.rabbitmq import connect_rabbitmq, close_rabbitmq, publish_match
from services.match_service.schemas import LikeCreate, LikeResult, LikeResponse, MatchResponse

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    await create_tables()
    await connect_rabbitmq()
    logger.info("Match service started")
    yield
    await close_rabbitmq()
    logger.info("Match service stopped")


app = FastAPI(title="Match Service", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/likes/", response_model=LikeResult, status_code=status.HTTP_201_CREATED)
async def create_like_endpoint(
    body: LikeCreate, session: AsyncSession = Depends(get_session)
) -> LikeResult:
    try:
        like, is_match, match = await process_like(
            session, body.from_user_id, body.to_user_id, body.to_profile_id
        )
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already liked")

    if is_match and match:
        try:
            await publish_match(body.from_user_id, body.to_user_id, str(match.id))
        except Exception as exc:
            logger.warning("Failed to publish match event: %s", exc)

    return LikeResult(
        like=LikeResponse.model_validate(like),
        is_match=is_match,
        match=MatchResponse.model_validate(match) if match else None,
    )


@app.get("/matches/{user_id}", response_model=List[MatchResponse])
async def get_matches(
    user_id: int, session: AsyncSession = Depends(get_session)
) -> List[MatchResponse]:
    matches = await get_user_matches(session, user_id)
    return matches
