"""LearningJourney ORM Model — derived from erm.dbml."""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class LearningMode(str, enum.Enum):
    SPRINT = "sprint"
    STANDARD = "standard"
    MASTERY = "mastery"


class SelfAssessedLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningJourney(Base):
    __tablename__ = "learning_journeys"
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_learning_journeys_user_subject"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    exam_date: Mapped[date | None] = mapped_column(Date)
    self_assessed_level: Mapped[str] = mapped_column(
        Enum(SelfAssessedLevel, name="self_assessed_level", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=SelfAssessedLevel.BEGINNER,
    )
    learning_mode: Mapped[str] = mapped_column(
        Enum(LearningMode, name="learning_mode", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=LearningMode.STANDARD,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
