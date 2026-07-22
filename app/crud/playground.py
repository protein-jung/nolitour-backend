import uuid

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
from app.schemas.playground import PlaygroundCreate


def get_playground(db: Session, playground_id: uuid.UUID) -> Playground | None:
    return db.get(Playground, playground_id)


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
