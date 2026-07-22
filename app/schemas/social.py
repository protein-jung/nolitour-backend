import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CommentCreate(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not (1 <= len(v) <= 1000):
            raise ValueError("댓글은 1~1000자여야 합니다.")
        return v


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    created_at: datetime
    author_nickname: str
    author_id: uuid.UUID


class LikeStatus(BaseModel):
    like_count: int
    liked_by_me: bool
