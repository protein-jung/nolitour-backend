import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.social import PlaygroundComment, PlaygroundLike


def get_like_status(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID | None) -> tuple[int, bool]:
    count = db.execute(
        select(func.count()).select_from(PlaygroundLike).where(PlaygroundLike.playground_id == playground_id)
    ).scalar_one()
    liked = False
    if user_id is not None:
        liked = (
            db.execute(
                select(PlaygroundLike).where(
                    PlaygroundLike.playground_id == playground_id,
                    PlaygroundLike.user_id == user_id,
                )
            ).scalar_one_or_none()
            is not None
        )
    return count, liked


def like_playground(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = db.execute(
        select(PlaygroundLike).where(
            PlaygroundLike.playground_id == playground_id,
            PlaygroundLike.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(PlaygroundLike(playground_id=playground_id, user_id=user_id))
    db.commit()


def unlike_playground(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = db.execute(
        select(PlaygroundLike).where(
            PlaygroundLike.playground_id == playground_id,
            PlaygroundLike.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()


def list_comments(db: Session, playground_id: uuid.UUID) -> list[PlaygroundComment]:
    stmt = (
        select(PlaygroundComment)
        .where(PlaygroundComment.playground_id == playground_id)
        .order_by(PlaygroundComment.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def create_comment(
    db: Session, playground_id: uuid.UUID, user_id: uuid.UUID, content: str
) -> PlaygroundComment:
    comment = PlaygroundComment(playground_id=playground_id, user_id=user_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_comment(db: Session, comment_id: uuid.UUID) -> PlaygroundComment | None:
    return db.get(PlaygroundComment, comment_id)


def delete_comment(db: Session, comment: PlaygroundComment) -> None:
    db.delete(comment)
    db.commit()
