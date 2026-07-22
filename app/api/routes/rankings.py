from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.playground import Playground
from app.models.user import User
from app.schemas.ranking import ReporterRankingItem

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/reporters", response_model=list[ReporterRankingItem])
def top_reporters(limit: int = 10, db: Session = Depends(get_db)):
    """놀이터 제보 개수 기준 제보왕 랭킹 (실시간 집계)"""
    count_col = func.count(Playground.id)
    stmt = (
        select(User.nickname, count_col.label("count"))
        .join(Playground, Playground.submitted_by_id == User.id)
        .group_by(User.id, User.nickname)
        .order_by(count_col.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        ReporterRankingItem(rank=i + 1, nickname=row.nickname, count=row.count)
        for i, row in enumerate(rows)
    ]
