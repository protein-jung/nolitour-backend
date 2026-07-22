import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.playground import (
    AgeGroup,
    EquipmentType,
    FenceType,
    ParkingType,
    PlaygroundSource,
    PlaygroundType,
    RestroomType,
    ShadeLevel,
    SurfaceType,
)


class PlaygroundImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_url: str
    is_primary: bool


class PlaygroundBase(BaseModel):
    name: str
    type: PlaygroundType | None = None
    age_groups: list[AgeGroup] | None = None
    address: str
    directions: str | None = None
    description: str | None = None
    latitude: float
    longitude: float
    operating_hours: str | None = None
    closed_days: str | None = None
    phone: str | None = None

    # 안전 정보
    surface_types: list[SurfaceType] | None = None
    shade_level: ShadeLevel | None = None
    restroom: RestroomType | None = None
    parking: ParkingType | None = None
    has_water_fountain: bool | None = None
    has_cctv: bool | None = None
    fence: FenceType | None = None
    stroller_accessible: bool | None = None
    wheelchair_accessible: bool | None = None

    # 놀이기구
    equipment: list[EquipmentType] | None = None


class PlaygroundCreate(PlaygroundBase):
    """사용자 직접 입력용 (source는 서버에서 user_submitted로 고정)"""


class PlaygroundOut(PlaygroundBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: PlaygroundSource
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    images: list[PlaygroundImageOut] = []

    # 목록(GET /playgrounds) 조회 시에는 채우지 않고, 단건 조회 시에만 계산해서 채운다.
    like_count: int | None = None
    liked_by_me: bool | None = None
    comment_count: int | None = None
    average_rating: float | None = None
    rating_count: int | None = None
