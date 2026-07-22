from pydantic import BaseModel


class ReporterRankingItem(BaseModel):
    rank: int
    nickname: str
    count: int
