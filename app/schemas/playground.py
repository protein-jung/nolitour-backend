import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.playground import (
    AccessLevel,
    AgeGroup,
    ConditionStatus,
    EquipmentType,
    FenceType,
    MoodTag,
    NatureFeature,
    NearbyFacility,
    ParkingType,
    PetPolicy,
    PlayDuration,
    PlaygroundSize,
    PlaygroundSource,
    PlaygroundType,
    RestroomType,
    RoadSafetyLevel,
    ShadeLevel,
    SmokingStatus,
    SurfaceType,
    WheeledAccessType,
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

    # 관리 상태 · 규모 · 놀이시간 · 추천
    condition_status: ConditionStatus | None = None
    size: PlaygroundSize | None = None
    play_duration: PlayDuration | None = None
    recommended_age: int | None = None  # 가장 추천하는 나이 (세)
    recommend_rating: int | None = None  # 1~5, 부모 추천도

    # 자연·반려동물·운영기간
    nature_features: list[NatureFeature] | None = None
    operating_season: str | None = None  # 예: "6월~8월"
    pet_policy: PetPolicy | None = None

    # 주변 시설 · 흡연 · 이동수단 · 접근성 · 안전
    nearby_facilities: list[NearbyFacility] | None = None
    smoking_status: SmokingStatus | None = None
    wheeled_access: list[WheeledAccessType] | None = None
    stroller_access_level: AccessLevel | None = None
    road_safety: RoadSafetyLevel | None = None

    # 분위기 태그
    mood_tags: list[MoodTag] | None = None

    @field_validator("recommended_age")
    @classmethod
    def validate_recommended_age(cls, v: int | None) -> int | None:
        if v is not None and not (0 <= v <= 15):
            raise ValueError("추천 나이는 0~15세 사이여야 합니다.")
        return v

    @field_validator("recommend_rating")
    @classmethod
    def validate_recommend_rating(cls, v: int | None) -> int | None:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("추천도는 1~5 사이여야 합니다.")
        return v


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

    # 로그인한 사용자가 후기를 남긴 적 있는 놀이터인지 (목록·단건 조회 모두에서 채워짐, 퀘스트 완료 마커 표시용)
    reviewed_by_me: bool = False
    # 로그인한 사용자가 GPS로 '왔다감' 체크인한 놀이터인지 (목록·단건 조회 모두에서 채워짐)
    visited_by_me: bool = False

    # 운영 중 자동으로 쌓이는 데이터 (제보자가 입력하지 않음)
    view_count: int = 0
    save_count: int | None = None
    saved_by_me: bool | None = None


class VisitCheckIn(BaseModel):
    latitude: float
    longitude: float


class VisitResult(BaseModel):
    visited_by_me: bool
    distance_m: float
