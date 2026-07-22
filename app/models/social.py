import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.playground import AgeGroup


class RiskTag(str, enum.Enum):
    """부모가 남기는 주의사항 태그 (복수 선택 가능)"""

    NEAR_ROAD = "near_road"  # 도로 인접
    MANY_BUGS = "many_bugs"  # 벌레 많음
    POORLY_MAINTAINED = "poorly_maintained"  # 관리 부족


class PlaygroundLike(Base):
    __tablename__ = "playground_likes"
    __table_args__ = (UniqueConstraint("playground_id", "user_id", name="uq_playground_like"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playground_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playgrounds.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PlaygroundComment(Base):
    """댓글이자 후기. rating이 채워지면 별점 후기로 취급한다."""

    __tablename__ = "playground_comments"
    __table_args__ = (CheckConstraint("rating IS NULL OR (rating BETWEEN 1 AND 5)", name="ck_comment_rating_range"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playground_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playgrounds.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # 1~5
    recommended_ages: Mapped[list[AgeGroup] | None] = mapped_column(
        ARRAY(Enum(AgeGroup, name="age_group")), nullable=True
    )
    risk_tags: Mapped[list[RiskTag] | None] = mapped_column(
        ARRAY(Enum(RiskTag, name="risk_tag")), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    author: Mapped["User"] = relationship()  # noqa: F821
    playground: Mapped["Playground"] = relationship()  # noqa: F821
    images: Mapped[list["PlaygroundCommentImage"]] = relationship(
        back_populates="comment", cascade="all, delete-orphan"
    )


class PlaygroundCommentImage(Base):
    __tablename__ = "playground_comment_images"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playground_comments.id", ondelete="CASCADE")
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    comment: Mapped[PlaygroundComment] = relationship(back_populates="images")
