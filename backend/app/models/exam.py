"""Exam ORM Model — derived from erm.dbml."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class ExamStatus(str, enum.Enum):
    """考試狀態列舉。"""

    PENDING = "PENDING"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"


class Exam(Base):
    """使用者考試（含 AI 生成模考、隨堂練習等）。

    對應 DBML 表：exams
    與 questions 一對多（透過 exam_id），與 answers 一對多。

    Attributes:
        user_id: 應試者（CASCADE）
        subject_id: 所屬科目
        institution_assignment_id: B2B 派題作業（可空）
        status: 狀態（PENDING / READY / IN_PROGRESS / SUBMITTED / FAILED）
        total_questions: 試卷題數
        difficulty_distribution / question_types: 出題參數
        score / correct_count: 結果
        custom_point_ratio / custom_bloom_ratio: 自訂出題權重
        historical_priority: 是否優先採用歷年題
        tenant_id: 多租戶隔離鍵
    """

    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    institution_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )
    status: Mapped[str] = mapped_column(
        Enum(ExamStatus, name="exam_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=ExamStatus.PENDING,
    )
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    passing_score: Mapped[int | None] = mapped_column(Integer)
    difficulty_distribution: Mapped[dict | None] = mapped_column(JSON)
    question_types: Mapped[list | None] = mapped_column(ARRAY(String))
    question_order_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="interleaved",
        comment="F19 題目排列模式：interleaved / sequential / grouped",
    )
    score: Mapped[int | None] = mapped_column(Integer)
    correct_count: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    custom_point_ratio: Mapped[dict | None] = mapped_column(JSON)
    custom_bloom_ratio: Mapped[dict | None] = mapped_column(JSON)
    historical_priority: Mapped[bool] = mapped_column(Boolean, default=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
