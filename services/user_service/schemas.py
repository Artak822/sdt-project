from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    user_id: int
    username: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    created_at: datetime
    last_active: datetime
    is_banned: bool

    model_config = {"from_attributes": True}
