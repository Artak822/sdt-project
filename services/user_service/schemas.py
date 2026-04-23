from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    user_id: int
    username: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: Optional[str]
    created_at: datetime
    last_active: datetime
    is_banned: bool


class ProfileCreate(BaseModel):
    user_id: int
    name: str
    age: int
    gender: str
    looking_for: str
    bio: Optional[str] = None
    city: Optional[str] = None
    age_range_min: int = 18
    age_range_max: int = 60
    photo_id: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    looking_for: Optional[str] = None
    age_range_min: Optional[int] = None
    age_range_max: Optional[int] = None
    photo_id: Optional[str] = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: UUID
    user_id: int
    name: str
    age: int
    gender: str
    bio: Optional[str]
    city: Optional[str]
    looking_for: str
    age_range_min: int
    age_range_max: int
    is_complete: bool
    photo_id: Optional[str]
    updated_at: datetime
