import uuid
from datetime import datetime

from pydantic import BaseModel


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
