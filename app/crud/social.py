import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.playground import AgeGroup, Playground
from app.models.social import PlaygroundComment, PlaygroundLike, RiskTag


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
    db: Session,
    playground_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
    *,
    rating: int | None = None,
    recommended_ages: list[AgeGroup] | None = None,
    risk_tags: list[RiskTag] | None = None,
) -> PlaygroundComment:
    comment = PlaygroundComment(
        playground_id=playground_id,
        user_id=user_id,
        content=content,
        rating=rating,
        recommended_ages=recommended_ages,
        risk_tags=risk_tags,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_rating_stats(db: Session, playground_id: uuid.UUID) -> tuple[float | None, int]:
    row = db.execute(
        select(func.avg(PlaygroundComment.rating), func.count(PlaygroundComment.rating)).where(
            PlaygroundComment.playground_id == playground_id,
            PlaygroundComment.rating.isnot(None),
        )
    ).one()
    avg, count = row
    return (round(float(avg), 1) if avg is not None else None), count


def get_comment(db: Session, comment_id: uuid.UUID) -> PlaygroundComment | None:
    return db.get(PlaygroundComment, comment_id)


def delete_comment(db: Session, comment: PlaygroundComment) -> None:
    db.delete(comment)
    db.commit()


def list_comments_by_user(db: Session, user_id: uuid.UUID) -> list[tuple[PlaygroundComment, str]]:
    """(댓글, 놀이터 이름) 목록을 최신순으로 반환한다."""
    stmt = (
        select(PlaygroundComment, Playground.name)
        .join(Playground, Playground.id == PlaygroundComment.playground_id)
        .where(PlaygroundComment.user_id == user_id)
        .order_by(PlaygroundComment.created_at.desc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def list_liked_playgrounds_by_user(db: Session, user_id: uuid.UUID) -> list[Playground]:
    stmt = (
        select(Playground)
        .join(PlaygroundLike, PlaygroundLike.playground_id == Playground.id)
        .where(PlaygroundLike.user_id == user_id)
        .order_by(PlaygroundLike.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
