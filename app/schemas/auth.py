import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class UserBrief(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    avatar_url: str | None = None
    phone: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
