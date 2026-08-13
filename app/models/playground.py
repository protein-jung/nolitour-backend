import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PlaygroundType(str, enum.Enum):
    """놀이터 유형 (초안 — 추후 조정 가능)"""

    APARTMENT = "apartment"  # 아파트 단지 내
    NEIGHBORHOOD_PARK = "neighborhood_park"  # 근린공원 내
    CHILDRENS_PARK = "childrens_park"  # 어린이공원 내
    SCHOOL = "school"  # 학교 부속
    INDOOR = "indoor"  # 실내 놀이터 (키즈카페 성격 제외, 무료/공공 시설 위주)
    THEME = "theme"  # 특수 테마 놀이터
    INCLUSIVE = "inclusive"  # 무장애·통합 놀이터
    RIVERSIDE = "riverside"  # 하천·수변 공원 내
    ETC = "etc"  # 기타


class AgeGroup(str, enum.Enum):
    """적합 연령 (초안 — 놀이터 하나가 여러 연령대를 가질 수 있음)"""

    INFANT = "infant"  # 영유아 0~3세
    TODDLER = "toddler"  # 유아 4~6세
    CHILD = "child"  # 어린이 7~9세
    PRETEEN = "preteen"  # 초등고학년 10~12세
    ALL_AGES = "all_ages"  # 전연령


class PlaygroundSource(str, enum.Enum):
    PUBLIC_DATA = "public_data"
    USER_SUBMITTED = "user_submitted"


class SurfaceType(str, enum.Enum):
    """바닥 재질 (복수 선택 가능)"""

    URETHANE = "urethane"  # 우레탄
    SAND = "sand"  # 모래
    GRASS = "grass"  # 잔디
    RUBBER_CHIP = "rubber_chip"  # 고무칩
    SOIL = "soil"  # 흙


class ShadeLevel(str, enum.Enum):
    """그늘 여부"""

    SUFFICIENT = "sufficient"  # 충분함
    MODERATE = "moderate"  # 보통
    NONE = "none"  # 없음


class RestroomType(str, enum.Enum):
    """화장실"""

    NONE = "none"  # 없음
    AVAILABLE = "available"  # 있음
    AVAILABLE_WITH_DIAPER_TABLE = "available_with_diaper_table"  # 기저귀 교환대 있음


class ParkingType(str, enum.Enum):
    """주차"""

    NONE = "none"  # 없음
    FREE = "free"  # 무료
    PAID = "paid"  # 유료


class AdmissionFeeType(str, enum.Enum):
    """이용료"""

    FREE = "free"  # 무료
    PAID = "paid"  # 유료


class FenceType(str, enum.Enum):
    """펜스"""

    FULL = "full"  # 완전 둘러짐
    PARTIAL = "partial"  # 부분 있음
    NONE = "none"  # 없음


class EquipmentType(str, enum.Enum):
    """놀이기구 (복수 선택 가능)"""

    SLIDE = "slide"  # 미끄럼틀
    SWING = "swing"  # 그네
    SEESAW = "seesaw"  # 시소
    ZIPLINE = "zipline"  # 집라인
    SAND_PLAY = "sand_play"  # 모래놀이
    TRAMPOLINE = "trampoline"  # 트램펄린
    CLIMBING = "climbing"  # 클라이밍
    WATER_PLAY = "water_play"  # 물놀이


class SportsFacility(str, enum.Enum):
    """부가 시설 (놀이터 주변에 함께 있는 운동·편의 시설, 복수 선택 가능)"""

    SOCCER_FIELD = "soccer_field"  # 축구장
    BASKETBALL_COURT = "basketball_court"  # 농구장
    BADMINTON_COURT = "badminton_court"  # 배드민턴장
    VOLLEYBALL_COURT = "volleyball_court"  # 배구장
    GRASS_FIELD = "grass_field"  # 잔디밭
    OUTDOOR_GYM = "outdoor_gym"  # 야외 운동기구
    GATEBALL_COURT = "gateball_court"  # 게이트볼장


class ConditionStatus(str, enum.Enum):
    """관리 상태"""

    VERY_CLEAN = "very_clean"  # 매우 깨끗함
    AVERAGE = "average"  # 보통
    NEEDS_CARE = "needs_care"  # 관리 필요


class PlaygroundSize(str, enum.Enum):
    """규모"""

    SMALL = "small"  # 소형
    MEDIUM = "medium"  # 중형
    LARGE = "large"  # 대형


class PlayDuration(str, enum.Enum):
    """예상 놀이시간"""

    MIN_30 = "min_30"  # 30분
    HOUR_1 = "hour_1"  # 1시간
    HOUR_2_PLUS = "hour_2_plus"  # 2시간 이상


class NatureFeature(str, enum.Enum):
    """자연친화 특징 (복수 선택 가능)"""

    MANY_TREES = "many_trees"  # 나무 많음
    SHADY = "shady"  # 그늘 많음
    IN_FOREST = "in_forest"  # 숲 속
    IN_PARK = "in_park"  # 공원 안


class PetPolicy(str, enum.Enum):
    """반려동물 출입"""

    ALLOWED = "allowed"  # 반려견 출입 가능
    NOT_ALLOWED = "not_allowed"  # 불가


class NearbyFacility(str, enum.Enum):
    """주변 시설 (복수 선택 가능)"""

    CONVENIENCE_STORE = "convenience_store"  # 편의점
    CAFE = "cafe"  # 카페
    RESTROOM = "restroom"  # 화장실
    PHARMACY = "pharmacy"  # 약국
    HOSPITAL = "hospital"  # 병원
    PARKING = "parking"  # 주차장


class SmokingStatus(str, enum.Enum):
    """흡연 관련"""

    MANY_SMOKERS = "many_smokers"  # 흡연자 많음
    NO_SMOKING_ZONE = "no_smoking_zone"  # 금연구역


class WheeledAccessType(str, enum.Enum):
    """자전거·킥보드 (복수 선택 가능)"""

    KICKBOARD = "kickboard"  # 킥보드 가능
    BICYCLE = "bicycle"  # 자전거 가능


class AccessLevel(str, enum.Enum):
    """접근성 등급 (유모차 등)"""

    EASY = "easy"  # 쉬움
    MODERATE = "moderate"  # 보통
    DIFFICULT = "difficult"  # 어려움


class RoadSafetyLevel(str, enum.Enum):
    """도로 인접 안전도"""

    VERY_SAFE = "very_safe"  # 매우 안전
    MODERATE = "moderate"  # 보통
    DANGEROUS = "dangerous"  # 위험


class MoodTag(str, enum.Enum):
    """놀이터 분위기 태그 (복수 선택 가능)"""

    QUIET = "quiet"  # 조용한
    ACTIVE = "active"  # 활동적인
    PHOTOGENIC = "photogenic"  # 사진 찍기 좋은
    SPACIOUS = "spacious"  # 넓은
    NEWLY_BUILT = "newly_built"  # 신설
    WELL_MAINTAINED = "well_maintained"  # 관리 잘됨
    HIDDEN_GEM = "hidden_gem"  # 숨은 명소
    RAINY_DAY_OK = "rainy_day_ok"  # 비 오는 날도 가능
    SUMMER_PICK = "summer_pick"  # 여름 추천
    WINTER_PICK = "winter_pick"  # 겨울 추천
    STROLLER_FRIENDLY = "stroller_friendly"  # 유모차 추천
    FIRST_PLAYGROUND = "first_playground"  # 첫 놀이터
    DATE_SPOT = "date_spot"  # 데이트 가능
    FOREST_VIBE = "forest_vibe"  # 숲속
    LOTS_TO_DO = "lots_to_do"  # 놀거리 많음


class Playground(Base):
    __tablename__ = "playgrounds"
    __table_args__ = (
        CheckConstraint(
            "recommended_age IS NULL OR (recommended_age BETWEEN 0 AND 15)",
            name="ck_playground_recommended_age",
        ),
        CheckConstraint(
            "recommend_rating IS NULL OR (recommend_rating BETWEEN 1 AND 5)",
            name="ck_playground_recommend_rating",
        ),
        CheckConstraint(
            "admission_fee IS NULL OR admission_fee >= 0",
            name="ck_playground_admission_fee",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[PlaygroundType | None] = mapped_column(
        Enum(PlaygroundType, name="playground_type"), nullable=True
    )
    age_groups: Mapped[list[AgeGroup] | None] = mapped_column(
        ARRAY(Enum(AgeGroup, name="age_group")), nullable=True
    )

    address: Mapped[str] = mapped_column(String(300), nullable=False)
    directions: Mapped[str | None] = mapped_column(Text, nullable=True)  # 단지 내 찾아가는 법
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)

    operating_hours: Mapped[str | None] = mapped_column(String(200), nullable=True)
    closed_days: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    admission_fee_type: Mapped[AdmissionFeeType | None] = mapped_column(
        Enum(AdmissionFeeType, name="admission_fee_type"), nullable=True
    )
    admission_fee: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 원 단위, 유료일 때만 의미 있음

    # 안전 정보
    surface_types: Mapped[list[SurfaceType] | None] = mapped_column(
        ARRAY(Enum(SurfaceType, name="surface_type")), nullable=True
    )
    shade_level: Mapped[ShadeLevel | None] = mapped_column(
        Enum(ShadeLevel, name="shade_level"), nullable=True
    )
    restroom: Mapped[RestroomType | None] = mapped_column(
        Enum(RestroomType, name="restroom_type"), nullable=True
    )
    parking: Mapped[ParkingType | None] = mapped_column(
        Enum(ParkingType, name="parking_type"), nullable=True
    )
    has_water_fountain: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    has_cctv: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    fence: Mapped[FenceType | None] = mapped_column(Enum(FenceType, name="fence_type"), nullable=True)
    stroller_accessible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    wheelchair_accessible: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # 놀이기구
    equipment: Mapped[list[EquipmentType] | None] = mapped_column(
        ARRAY(Enum(EquipmentType, name="equipment_type")), nullable=True
    )

    # 부가 시설 (축구장·농구장 등 함께 있는 운동 시설)
    sports_facilities: Mapped[list[SportsFacility] | None] = mapped_column(
        ARRAY(Enum(SportsFacility, name="sports_facility")), nullable=True
    )

    # 관리 상태 · 규모 · 놀이시간 · 추천
    condition_status: Mapped[ConditionStatus | None] = mapped_column(
        Enum(ConditionStatus, name="condition_status"), nullable=True
    )
    size: Mapped[PlaygroundSize | None] = mapped_column(
        Enum(PlaygroundSize, name="playground_size"), nullable=True
    )
    play_duration: Mapped[PlayDuration | None] = mapped_column(
        Enum(PlayDuration, name="play_duration"), nullable=True
    )
    recommended_age: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 가장 추천하는 나이(세)
    recommend_rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 1~5, 부모 추천도

    # 자연·반려동물·운영기간
    nature_features: Mapped[list[NatureFeature] | None] = mapped_column(
        ARRAY(Enum(NatureFeature, name="nature_feature")), nullable=True
    )
    operating_season: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 예: "6월~8월"
    pet_policy: Mapped[PetPolicy | None] = mapped_column(
        Enum(PetPolicy, name="pet_policy"), nullable=True
    )

    # 주변 시설 · 흡연 · 이동수단 · 접근성 · 안전
    nearby_facilities: Mapped[list[NearbyFacility] | None] = mapped_column(
        ARRAY(Enum(NearbyFacility, name="nearby_facility")), nullable=True
    )
    smoking_status: Mapped[SmokingStatus | None] = mapped_column(
        Enum(SmokingStatus, name="smoking_status"), nullable=True
    )
    wheeled_access: Mapped[list[WheeledAccessType] | None] = mapped_column(
        ARRAY(Enum(WheeledAccessType, name="wheeled_access_type")), nullable=True
    )
    stroller_access_level: Mapped[AccessLevel | None] = mapped_column(
        Enum(AccessLevel, name="access_level"), nullable=True
    )
    road_safety: Mapped[RoadSafetyLevel | None] = mapped_column(
        Enum(RoadSafetyLevel, name="road_safety_level"), nullable=True
    )

    # 분위기 태그
    mood_tags: Mapped[list[MoodTag] | None] = mapped_column(
        ARRAY(Enum(MoodTag, name="mood_tag")), nullable=True
    )

    # 운영 중 자동으로 쌓이는 데이터
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    source: Mapped[PlaygroundSource] = mapped_column(
        Enum(PlaygroundSource, name="playground_source"),
        nullable=False,
        default=PlaygroundSource.PUBLIC_DATA,
    )
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 공공데이터 원본 고유번호
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    submitted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    images: Mapped[list["PlaygroundImage"]] = relationship(
        back_populates="playground", cascade="all, delete-orphan"
    )


class PlaygroundImage(Base):
    __tablename__ = "playground_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playground_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playgrounds.id", ondelete="CASCADE")
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    playground: Mapped[Playground] = relationship(back_populates="images")
