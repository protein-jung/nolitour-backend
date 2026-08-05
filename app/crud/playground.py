import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.playground import (
    AgeGroup,
    EquipmentType,
    ParkingType,
    Playground,
    PlaygroundSource,
    RestroomType,
    ShadeLevel,
)
from app.models.social import PlaygroundComment, PlaygroundEditLog, PlaygroundLike, PlaygroundSave, PlaygroundView
from app.schemas.playground import PlaygroundCreate, PlaygroundUpdate

ACTIVE_VIEWER_WINDOW_MINUTES = 10

# 인기 점수 가중치: 저장 > 좋아요 > 평균 별점(0~5를 10배해 최대 50점) > 조회수
LIKE_WEIGHT = 3
SAVE_WEIGHT = 4
RATING_WEIGHT = 10


def _popularity_score_expr():
    """좋아요·저장·조회수·평균 별점을 가중합한 인기 점수 SQL 표현식.
    order_by에만 쓸 때는 서브쿼리를 select 목록에 넣지 않아도 된다."""
    like_sq = (
        select(PlaygroundLike.playground_id, func.count().label("count"))
        .group_by(PlaygroundLike.playground_id)
        .subquery()
    )
    save_sq = (
        select(PlaygroundSave.playground_id, func.count().label("count"))
        .group_by(PlaygroundSave.playground_id)
        .subquery()
    )
    rating_sq = (
        select(PlaygroundComment.playground_id, func.avg(PlaygroundComment.rating).label("avg_rating"))
        .where(PlaygroundComment.rating.isnot(None))
        .group_by(PlaygroundComment.playground_id)
        .subquery()
    )
    score_expr = (
        func.coalesce(like_sq.c.count, 0) * LIKE_WEIGHT
        + func.coalesce(save_sq.c.count, 0) * SAVE_WEIGHT
        + Playground.view_count
        + func.coalesce(rating_sq.c.avg_rating, 0) * RATING_WEIGHT
    )
    joins = [
        (like_sq, like_sq.c.playground_id == Playground.id),
        (save_sq, save_sq.c.playground_id == Playground.id),
        (rating_sq, rating_sq.c.playground_id == Playground.id),
    ]
    return score_expr, joins


def get_playground(db: Session, playground_id: uuid.UUID) -> Playground | None:
    return db.get(Playground, playground_id)


def record_view(db: Session, playground: Playground, viewer_id: uuid.UUID | None) -> None:
    """상세 조회 시 카운터를 올리고, '지금 보는 중' 근사치를 위한 조회 기록도 남긴다."""
    playground.view_count += 1
    db.add(PlaygroundView(playground_id=playground.id, viewer_id=viewer_id))
    db.commit()


def get_active_viewer_counts(
    db: Session, playground_ids: list[uuid.UUID], *, window_minutes: int = ACTIVE_VIEWER_WINDOW_MINUTES
) -> dict[uuid.UUID, int]:
    """최근 N분 내 조회 기록 수를 놀이터별로 집계해 '지금 보는 중' 인원수의 근사치로 사용한다."""
    if not playground_ids:
        return {}
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    stmt = (
        select(PlaygroundView.playground_id, func.count().label("count"))
        .where(PlaygroundView.playground_id.in_(playground_ids), PlaygroundView.viewed_at >= cutoff)
        .group_by(PlaygroundView.playground_id)
    )
    return {row.playground_id: row.count for row in db.execute(stmt).all()}


def list_playgrounds(
    db: Session,
    *,
    min_lat: float | None = None,
    max_lat: float | None = None,
    min_lng: float | None = None,
    max_lng: float | None = None,
    age_groups: list[AgeGroup] | None = None,
    has_shade: bool = False,
    has_parking: bool = False,
    has_restroom: bool = False,
    equipment: list[EquipmentType] | None = None,
    sort: str | None = None,
    limit: int = 500,
) -> list[Playground]:
    stmt = select(Playground)
    if min_lat is not None:
        stmt = stmt.where(Playground.latitude >= min_lat)
    if max_lat is not None:
        stmt = stmt.where(Playground.latitude <= max_lat)
    if min_lng is not None:
        stmt = stmt.where(Playground.longitude >= min_lng)
    if max_lng is not None:
        stmt = stmt.where(Playground.longitude <= max_lng)
    if age_groups:
        stmt = stmt.where(Playground.age_groups.overlap(age_groups))
    if has_shade:
        stmt = stmt.where(Playground.shade_level.in_([ShadeLevel.SUFFICIENT, ShadeLevel.MODERATE]))
    if has_parking:
        stmt = stmt.where(Playground.parking.in_([ParkingType.FREE, ParkingType.PAID]))
    if has_restroom:
        stmt = stmt.where(
            Playground.restroom.in_([RestroomType.AVAILABLE, RestroomType.AVAILABLE_WITH_DIAPER_TABLE])
        )
    if equipment:
        stmt = stmt.where(Playground.equipment.overlap(equipment))
    if sort == "popular":
        score_expr, joins = _popularity_score_expr()
        for target, on_clause in joins:
            stmt = stmt.outerjoin(target, on_clause)
        stmt = stmt.order_by(score_expr.desc())
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_popular_playgrounds(db: Session, limit: int = 10) -> list[tuple[Playground, float]]:
    """인기 점수 상위 놀이터 목록. (놀이터, 점수) 튜플로 반환한다 (인기 놀이터 랭킹 페이지용)."""
    score_expr, joins = _popularity_score_expr()
    stmt = select(Playground, score_expr.label("score"))
    for target, on_clause in joins:
        stmt = stmt.outerjoin(target, on_clause)
    stmt = stmt.order_by(score_expr.desc()).limit(limit)
    return [(row[0], float(row[1])) for row in db.execute(stmt).all()]


def list_playgrounds_by_submitter(db: Session, submitted_by_id: uuid.UUID) -> list[Playground]:
    stmt = (
        select(Playground)
        .where(Playground.submitted_by_id == submitted_by_id)
        .order_by(Playground.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def create_user_playground(
    db: Session, data: PlaygroundCreate, *, submitted_by_id: uuid.UUID
) -> Playground:
    playground = Playground(
        **data.model_dump(),
        source=PlaygroundSource.USER_SUBMITTED,
        is_verified=False,
        submitted_by_id=submitted_by_id,
    )
    db.add(playground)
    db.commit()
    db.refresh(playground)
    return playground


def _serialize_field_value(value: object) -> object:
    if isinstance(value, list):
        return sorted((v.value if hasattr(v, "value") else v for v in value), key=str)
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "value"):
        return value.value
    return value


def _field_values_differ(old_value: object, new_value: object) -> bool:
    if isinstance(old_value, Decimal):
        old_value = float(old_value)
    if isinstance(new_value, Decimal):
        new_value = float(new_value)
    if isinstance(old_value, float) or isinstance(new_value, float):
        # Numeric(9,6) 컬럼 왕복 시 발생하는 부동소수점 오차 때문에 소수 6자리로 반올림해 비교한다.
        return round(old_value or 0, 6) != round(new_value or 0, 6)
    if isinstance(old_value, list) or isinstance(new_value, list):
        return set(old_value or []) != set(new_value or [])
    return old_value != new_value


def update_playground(
    db: Session, playground: Playground, data: PlaygroundUpdate, *, editor_id: uuid.UUID
) -> Playground:
    """로그인한 사용자 누구나 놀이터 정보를 수정할 수 있다 (나무위키 스타일).
    바뀐 필드만 골라 PlaygroundEditLog에 old/new 값을 남기고 적용한다."""
    changes: dict[str, dict[str, object]] = {}
    for field, new_value in data.model_dump().items():
        old_value = getattr(playground, field)
        if _field_values_differ(old_value, new_value):
            changes[field] = {
                "old": _serialize_field_value(old_value),
                "new": _serialize_field_value(new_value),
            }
            setattr(playground, field, new_value)

    if changes:
        db.add(PlaygroundEditLog(playground_id=playground.id, editor_id=editor_id, changes=changes))
        db.commit()
        db.refresh(playground)
    return playground


def list_edit_logs(db: Session, playground_id: uuid.UUID, limit: int = 50) -> list[PlaygroundEditLog]:
    stmt = (
        select(PlaygroundEditLog)
        .where(PlaygroundEditLog.playground_id == playground_id)
        .order_by(PlaygroundEditLog.created_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def list_playgrounds_for_admin(db: Session, *, is_verified: bool | None = None) -> list[Playground]:
    stmt = select(Playground).order_by(Playground.created_at.desc())
    if is_verified is not None:
        stmt = stmt.where(Playground.is_verified == is_verified)
    return list(db.execute(stmt).scalars().all())


def verify_playground(db: Session, playground: Playground) -> Playground:
    playground.is_verified = True
    db.commit()
    db.refresh(playground)
    return playground


def unverify_playground(db: Session, playground: Playground) -> Playground:
    playground.is_verified = False
    db.commit()
    db.refresh(playground)
    return playground


def delete_playground(db: Session, playground: Playground) -> None:
    db.delete(playground)
    db.commit()
