import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.playground import PlaygroundOut


class AdminStats(BaseModel):
    total_playgrounds: int
    pending_playgrounds: int
    total_users: int
    total_comments: int


class AdminUserOut(BaseModel):
    id: uuid.UUID
    phone: str
    name: str
    nickname: str
    is_admin: bool
    created_at: datetime
    playground_count: int


class AdminUserUpdate(BaseModel):
    is_admin: bool


class UserActivityComment(BaseModel):
    id: uuid.UUID
    content: str
    rating: int | None
    created_at: datetime
    playground_id: uuid.UUID
    playground_name: str


class UserActivity(BaseModel):
    user: AdminUserOut
    submitted_playgrounds: list[PlaygroundOut]
    comments: list[UserActivityComment]
    liked_playgrounds: list[PlaygroundOut]
