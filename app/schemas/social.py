import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.playground import AgeGroup
from app.models.social import RiskTag


class CommentCreate(BaseModel):
    content: str
    rating: int | None = None  # 1~5, 채워지면 별점 후기로 취급
    recommended_ages: list[AgeGroup] | None = None
    risk_tags: list[RiskTag] | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 1000):
            raise ValueError("댓글은 1~1000자여야 합니다.")
        return v

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("별점은 1~5 사이여야 합니다.")
        return v


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    rating: int | None = None
    recommended_ages: list[AgeGroup] | None = None
    risk_tags: list[RiskTag] | None = None
    created_at: datetime
    author_nickname: str
    author_id: uuid.UUID


class LikeStatus(BaseModel):
    like_count: int
    liked_by_me: bool
