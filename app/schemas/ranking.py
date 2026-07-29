import uuid

from pydantic import BaseModel


class ReporterRankingItem(BaseModel):
    rank: int
    user_id: uuid.UUID
    nickname: str
    count: int
