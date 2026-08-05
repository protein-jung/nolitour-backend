from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import playground as playground_crud
from app.crud import social as social_crud
from app.models.playground import Playground
from app.models.user import User
from app.schemas.ranking import PlaygroundRankingItem, ReporterRankingItem

router = APIRouter(prefix="/rankings", tags=["rankings"])


@router.get("/reporters", response_model=list[ReporterRankingItem])
def top_reporters(limit: int = 10, db: Session = Depends(get_db)):
    """놀이터 제보 개수 기준 제보왕 랭킹 (실시간 집계)"""
    count_col = func.count(Playground.id)
    stmt = (
        select(User.id, User.nickname, count_col.label("count"))
        .join(Playground, Playground.submitted_by_id == User.id)
        .group_by(User.id, User.nickname)
        .order_by(count_col.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        ReporterRankingItem(rank=i + 1, user_id=row.id, nickname=row.nickname, count=row.count)
        for i, row in enumerate(rows)
    ]


@router.get("/visitors", response_model=list[ReporterRankingItem])
def top_visitors(limit: int = 10, db: Session = Depends(get_db)):
    """놀이터 GPS 체크인('왔다감') 개수 기준 랭킹 (실시간 집계)"""
    rows = social_crud.get_visitor_ranking(db, limit)
    return [
        ReporterRankingItem(rank=i + 1, user_id=user_id, nickname=nickname, count=count)
        for i, (user_id, nickname, count) in enumerate(rows)
    ]


@router.get("/playgrounds", response_model=list[PlaygroundRankingItem])
def top_playgrounds(limit: int = 10, db: Session = Depends(get_db)):
    """좋아요·저장·조회수·평균 별점을 가중합한 인기 점수 기준 놀이터 랭킹"""
    rows = playground_crud.get_popular_playgrounds(db, limit)
    return [
        PlaygroundRankingItem(rank=i + 1, playground_id=p.id, name=p.name, address=p.address, score=round(score, 1))
        for i, (p, score) in enumerate(rows)
    ]
