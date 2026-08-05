import uuid
from decimal import Decimal

from sqlalchemy import select
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
from app.models.social import PlaygroundEditLog
from app.schemas.playground import PlaygroundCreate, PlaygroundUpdate


def get_playground(db: Session, playground_id: uuid.UUID) -> Playground | None:
    return db.get(Playground, playground_id)


def increment_view_count(db: Session, playground: Playground) -> None:
    playground.view_count += 1
    db.commit()


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
    stmt = stmt.limit(limit)
    return list(db.execute(stmt).scalars().all())


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
