import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.playground import AgeGroup, PlaygroundSource, PlaygroundType


class PlaygroundImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    is_primary: bool


class PlaygroundBase(BaseModel):
    name: str
    type: PlaygroundType | None = None
    age_groups: list[AgeGroup] | None = None
    address: str
    directions: str | None = None
    description: str | None = None
    latitude: float
    longitude: float
    operating_hours: str | None = None
    closed_days: str | None = None
    phone: str | None = None


class PlaygroundCreate(PlaygroundBase):
    """사용자 직접 입력용 (source는 서버에서 user_submitted로 고정)"""


class PlaygroundOut(PlaygroundBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: PlaygroundSource
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    images: list[PlaygroundImageOut] = []
