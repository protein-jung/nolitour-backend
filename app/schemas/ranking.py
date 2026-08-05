import uuid

from pydantic import BaseModel


class ReporterRankingItem(BaseModel):
    rank: int
    user_id: uuid.UUID
    nickname: str
    count: int


class PlaygroundRankingItem(BaseModel):
    rank: int
    playground_id: uuid.UUID
    name: str
    address: str
    score: float
