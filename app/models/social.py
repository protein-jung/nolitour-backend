import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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


class PlaygroundEditLog(Base):
    """놀이터 정보 수정 이력 (나무위키 스타일 공동 편집). 변경된 필드만 old/new 값으로 기록한다."""

    __tablename__ = "playground_edit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    playground_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playgrounds.id", ondelete="CASCADE")
    )
    editor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    changes: Mapped[dict] = mapped_column(JSONB, nullable=False)  # {field: {"old": ..., "new": ...}}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    editor: Mapped["User"] = relationship()  # noqa: F821


class PlaygroundSave(Base):
    """놀이터 저장(북마크). 좋아요와 별개로 '나중에 다시 보기' 용도."""

    __tablename__ = "playground_saves"
    __table_args__ = (UniqueConstraint("playground_id", "user_id", name="uq_playground_save"),)

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


class PlaygroundVisit(Base):
    """GPS 기반 '왔다감' 체크인. 같은 사용자가 같은 놀이터를 여러 번 체크인해도 한 행만 유지한다."""

    __tablename__ = "playground_visits"
    __table_args__ = (UniqueConstraint("playground_id", "user_id", name="uq_playground_visit"),)

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


class CommentLike(Base):
    """댓글·후기(피드 게시물)에 대한 좋아요"""

    __tablename__ = "comment_likes"
    __table_args__ = (UniqueConstraint("comment_id", "user_id", name="uq_comment_like"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playground_comments.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CommentReply(Base):
    """댓글·후기(피드 게시물)에 대한 답글"""

    __tablename__ = "comment_replies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("playground_comments.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    author: Mapped["User"] = relationship()  # noqa: F821


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
