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
    """三層題目抽取分層（T2 / T3，T1 直接進 questions）。"""

    T2 = "T2"
    T3 = "T3"


class QuestionCandidateDecision(str, enum.Enum):
    """候選題審核決定列舉。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class QuestionCandidate(Base):
    """EPIC-035 三層抽題 T2/T3 候選題暫存。

    對應 DBML 表：question_candidates
    Approve 後可晉升為正式 Question；Reject 為廢棄。

    Attributes:
        resource_id: 來源資源（CASCADE）
        tenant_id: 多租戶隔離鍵
        question_text: 題幹
        options: JSONB 選項陣列
        ai_inferred_answer: AI 推論答案
        confidence: AI 信心度（0-1）
        source_page: 來源頁碼
        figure_refs: 引用圖檔清單
        tier: T2 / T3
        decision: pending / approved / rejected
        decided_at: 審核時間
    """

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
