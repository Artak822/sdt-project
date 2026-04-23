from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    profile_id: UUID
    primary_score: Decimal
    behavioral_score: Decimal
    combined_score: Decimal
    calculated_at: datetime
