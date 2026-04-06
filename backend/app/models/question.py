"""Question ORM Model — derived from erm.dbml."""

import enum

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN = "fill_in"
    CALCULATION = "calculation"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BloomCategory(str, enum.Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id")
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(
        Enum(QuestionType, name="question_type", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=QuestionType.SINGLE_CHOICE,
    )
    difficulty: Mapped[str] = mapped_column(
        Enum(DifficultyLevel, name="difficulty_level", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=DifficultyLevel.MEDIUM,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str | None] = mapped_column(Text)
    option_b: Mapped[str | None] = mapped_column(Text)
    option_c: Mapped[str | None] = mapped_column(Text)
    option_d: Mapped[str | None] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(String(10), nullable=False)
    bloom_category: Mapped[str | None] = mapped_column(
        Enum(BloomCategory, name="bloom_category", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
    )
    explanation: Mapped[str | None] = mapped_column(Text)
    source_citation: Mapped[str | None] = mapped_column(Text)
    historical_source: Mapped[str | None] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(
        String(20), server_default="historical"
    )
    quality_flag: Mapped[str | None] = mapped_column(String(20), default="ok")
    flag_reason: Mapped[str | None] = mapped_column(Text)
    validation_model: Mapped[str | None] = mapped_column(String(50))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_reason: Mapped[str | None] = mapped_column(String(50))
    suggested_node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id")
    )
