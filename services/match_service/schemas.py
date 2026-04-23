from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LikeCreate(BaseModel):
    from_user_id: int
    to_user_id: int
    to_profile_id: UUID


class LikeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    from_user_id: int
    to_user_id: int
    is_mutual: bool
    created_at: datetime


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user1_id: int
    user2_id: int
    created_at: datetime
    chat_started: bool


class LikeResult(BaseModel):
    like: LikeResponse
    is_match: bool
    match: Optional[MatchResponse] = None
