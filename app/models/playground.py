import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
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


class Playground(Base):
    __tablename__ = "playgrounds"

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
