import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user_optional
from app.crud import social as social_crud
from app.models.user import User
from app.schemas.feed import FeedItem

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=list[FeedItem])
def get_feed(
    limit: int = 20,
    offset: int = 0,
    author_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """전체 놀이터의 댓글·후기를 최신순으로 모아 보여주는 피드. author_id 지정 시 해당 사용자 글만."""
    comments = social_crud.list_feed(db, limit=limit, offset=offset, author_id=author_id)
    comment_ids = [c.id for c in comments]
    like_counts = social_crud.get_comment_like_counts(db, comment_ids)
    reply_counts = social_crud.get_comment_reply_counts(db, comment_ids)
    liked_ids = (
        social_crud.list_liked_comment_ids(db, current_user.id, comment_ids) if current_user else set()
    )
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
            like_count=like_counts.get(c.id, 0),
            liked_by_me=c.id in liked_ids,
            reply_count=reply_counts.get(c.id, 0),
        )
        for c in comments
    ]
