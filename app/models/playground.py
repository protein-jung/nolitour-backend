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

    source: Mapped[PlaygroundSource] = mapped_column(
        Enum(PlaygroundSource, name="playground_source"),
        nullable=False,
        default=PlaygroundSource.PUBLIC_DATA,
    )
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 공공데이터 원본 고유번호
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
