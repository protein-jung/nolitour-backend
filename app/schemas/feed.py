import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.playground import AgeGroup
from app.models.social import RiskTag
from app.schemas.social import CommentImageOut


class FeedItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    rating: int | None = None
    recommended_ages: list[AgeGroup] | None = None
    risk_tags: list[RiskTag] | None = None
    created_at: datetime
    author_nickname: str
    author_id: uuid.UUID
    images: list[CommentImageOut] = []

    playground_id: uuid.UUID
    playground_name: str
    playground_address: str
    playground_latitude: float
    playground_longitude: float
