"""QuestionCandidate ORM Model — EPIC-035 M2 三層題目抽取 T2/T3 暫存。

T1 題目直接進 questions 表；T2/T3 暫存此處等用戶審視。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class QuestionCandidateTier(str, enum.Enum):
    T2 = "T2"
    T3 = "T3"


class QuestionCandidateDecision(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class QuestionCandidate(Base):
    __tablename__ = "question_candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
    ai_inferred_answer: Mapped[str | None] = mapped_column(String(10))
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2))
    source_page: Mapped[int | None] = mapped_column(Integer)
    figure_refs: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    tier: Mapped[str] = mapped_column(
        Enum(QuestionCandidateTier, name="question_candidate_tier",
             create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(
        Enum(QuestionCandidateDecision, name="question_candidate_decision",
             create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=QuestionCandidateDecision.PENDING,
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
