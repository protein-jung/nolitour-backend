from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import social as social_crud
from app.schemas.feed import FeedItem

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=list[FeedItem])
def get_feed(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    """전체 놀이터의 댓글·후기를 최신순으로 모아 보여주는 피드"""
    comments = social_crud.list_feed(db, limit=limit, offset=offset)
    return [
        FeedItem(
            id=c.id,
            content=c.content,
            rating=c.rating,
            recommended_ages=c.recommended_ages,
            risk_tags=c.risk_tags,
            created_at=c.created_at,
            author_nickname=c.author.nickname,
            author_id=c.user_id,
            images=list(c.images),
            playground_id=c.playground_id,
            playground_name=c.playground.name,
            playground_address=c.playground.address,
            playground_latitude=c.playground.latitude,
            playground_longitude=c.playground.longitude,
        )
        for c in comments
    ]
