import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.playground import AgeGroup, Playground
from app.models.social import (
    CommentLike,
    CommentReply,
    PlaygroundComment,
    PlaygroundCommentImage,
    PlaygroundLike,
    PlaygroundSave,
    PlaygroundVisit,
    RiskTag,
)
from app.models.user import User


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


def get_save_status(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID | None) -> tuple[int, bool]:
    count = db.execute(
        select(func.count()).select_from(PlaygroundSave).where(PlaygroundSave.playground_id == playground_id)
    ).scalar_one()
    saved = False
    if user_id is not None:
        saved = (
            db.execute(
                select(PlaygroundSave).where(
                    PlaygroundSave.playground_id == playground_id,
                    PlaygroundSave.user_id == user_id,
                )
            ).scalar_one_or_none()
            is not None
        )
    return count, saved


def save_playground(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = db.execute(
        select(PlaygroundSave).where(
            PlaygroundSave.playground_id == playground_id,
            PlaygroundSave.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(PlaygroundSave(playground_id=playground_id, user_id=user_id))
    db.commit()


def unsave_playground(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = db.execute(
        select(PlaygroundSave).where(
            PlaygroundSave.playground_id == playground_id,
            PlaygroundSave.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()


def list_saved_playgrounds_by_user(db: Session, user_id: uuid.UUID) -> list[Playground]:
    stmt = (
        select(Playground)
        .join(PlaygroundSave, PlaygroundSave.playground_id == Playground.id)
        .where(PlaygroundSave.user_id == user_id)
        .order_by(PlaygroundSave.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


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


def add_comment_image(db: Session, comment_id: uuid.UUID, image_url: str) -> PlaygroundCommentImage:
    image = PlaygroundCommentImage(comment_id=comment_id, image_url=image_url)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def list_reviewed_playground_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    """사용자가 댓글·후기를 남긴 적 있는 놀이터 id 집합 (지도 퀘스트 완료 마커 표시용)"""
    stmt = select(PlaygroundComment.playground_id).distinct().where(PlaygroundComment.user_id == user_id)
    return set(db.execute(stmt).scalars().all())


def list_visited_playground_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    """사용자가 GPS 체크인('왔다감')한 놀이터 id 집합"""
    stmt = select(PlaygroundVisit.playground_id).where(PlaygroundVisit.user_id == user_id)
    return set(db.execute(stmt).scalars().all())


def list_visits_by_user(db: Session, user_id: uuid.UUID) -> list[tuple[PlaygroundVisit, str]]:
    """(체크인 기록, 놀이터 이름) 목록을 최신순으로 반환한다."""
    stmt = (
        select(PlaygroundVisit, Playground.name)
        .join(Playground, Playground.id == PlaygroundVisit.playground_id)
        .where(PlaygroundVisit.user_id == user_id)
        .order_by(PlaygroundVisit.created_at.desc())
    )
    return [(row[0], row[1]) for row in db.execute(stmt).all()]


def create_visit(db: Session, playground_id: uuid.UUID, user_id: uuid.UUID) -> PlaygroundVisit:
    """이미 체크인한 놀이터면 기존 행을 그대로 반환한다 (idempotent)."""
    existing = db.execute(
        select(PlaygroundVisit).where(
            PlaygroundVisit.playground_id == playground_id,
            PlaygroundVisit.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    visit = PlaygroundVisit(playground_id=playground_id, user_id=user_id)
    db.add(visit)
    db.commit()
    db.refresh(visit)
    return visit


def get_visitor_ranking(db: Session, limit: int) -> list[tuple[uuid.UUID, str, int]]:
    """놀이터 체크인(왔다감) 개수 기준 랭킹 (사용자 id, 닉네임, 방문한 놀이터 수)"""
    count_col = func.count(PlaygroundVisit.playground_id.distinct())
    stmt = (
        select(User.id, User.nickname, count_col.label("count"))
        .join(PlaygroundVisit, PlaygroundVisit.user_id == User.id)
        .group_by(User.id, User.nickname)
        .order_by(count_col.desc())
        .limit(limit)
    )
    return [(row.id, row.nickname, row.count) for row in db.execute(stmt).all()]


def list_feed(
    db: Session, limit: int, offset: int, author_id: uuid.UUID | None = None
) -> list[PlaygroundComment]:
    """전체 놀이터의 댓글·후기를 최신순으로 반환한다 (피드용). author_id 지정 시 해당 사용자 글만."""
    stmt = select(PlaygroundComment).order_by(PlaygroundComment.created_at.desc()).limit(limit).offset(offset)
    if author_id is not None:
        stmt = stmt.where(PlaygroundComment.user_id == author_id)
    return list(db.execute(stmt).scalars().all())


def get_comment_like_status(db: Session, comment_id: uuid.UUID, user_id: uuid.UUID | None) -> tuple[int, bool]:
    count = db.execute(
        select(func.count()).select_from(CommentLike).where(CommentLike.comment_id == comment_id)
    ).scalar_one()
    liked = False
    if user_id is not None:
        liked = (
            db.execute(
                select(CommentLike).where(
                    CommentLike.comment_id == comment_id, CommentLike.user_id == user_id
                )
            ).scalar_one_or_none()
            is not None
        )
    return count, liked


def like_comment(db: Session, comment_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = db.execute(
        select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
    ).scalar_one_or_none()
    if existing:
        return
    db.add(CommentLike(comment_id=comment_id, user_id=user_id))
    db.commit()


def unlike_comment(db: Session, comment_id: uuid.UUID, user_id: uuid.UUID) -> None:
    existing = db.execute(
        select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        db.commit()


def list_comment_replies(db: Session, comment_id: uuid.UUID) -> list[CommentReply]:
    stmt = (
        select(CommentReply)
        .where(CommentReply.comment_id == comment_id)
        .order_by(CommentReply.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def create_comment_reply(db: Session, comment_id: uuid.UUID, user_id: uuid.UUID, content: str) -> CommentReply:
    reply = CommentReply(comment_id=comment_id, user_id=user_id, content=content)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def get_comment_reply(db: Session, reply_id: uuid.UUID) -> CommentReply | None:
    return db.get(CommentReply, reply_id)


def delete_comment_reply(db: Session, reply: CommentReply) -> None:
    db.delete(reply)
    db.commit()


def get_comment_like_counts(db: Session, comment_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not comment_ids:
        return {}
    stmt = (
        select(CommentLike.comment_id, func.count().label("count"))
        .where(CommentLike.comment_id.in_(comment_ids))
        .group_by(CommentLike.comment_id)
    )
    return {row.comment_id: row.count for row in db.execute(stmt).all()}


def get_comment_reply_counts(db: Session, comment_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not comment_ids:
        return {}
    stmt = (
        select(CommentReply.comment_id, func.count().label("count"))
        .where(CommentReply.comment_id.in_(comment_ids))
        .group_by(CommentReply.comment_id)
    )
    return {row.comment_id: row.count for row in db.execute(stmt).all()}


def list_liked_comment_ids(db: Session, user_id: uuid.UUID, comment_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not comment_ids:
        return set()
    stmt = select(CommentLike.comment_id).where(
        CommentLike.user_id == user_id, CommentLike.comment_id.in_(comment_ids)
    )
    return set(db.execute(stmt).scalars().all())
