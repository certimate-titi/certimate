"""Question ORM Model — derived from erm.dbml."""

import enum

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class QuestionType(str, enum.Enum):
    """題型列舉（單選 / 複選 / 填充 / 計算）。"""

    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN = "fill_in"
    CALCULATION = "calculation"


class DifficultyLevel(str, enum.Enum):
    """難度列舉（easy / medium / hard）。"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BloomCategory(str, enum.Enum):
    """Bloom 認知層級列舉（remember / understand / apply / analyze / evaluate / create）。"""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class Question(Base):
    """題目主檔（含考古題 / AI 生成 / 個人題庫多種來源）。

    對應 DBML 表：questions
    Constraint：exam_id 與 historical_exam_id 必有其一不為 NULL。

    Attributes:
        exam_id: 使用者考試 FK（AI 生成 / 模擬考）
        historical_exam_id: 歷史考試 FK（爬蟲匯入考古題）
        node_id: 對應知識節點
        question_number: 題號
        type: 題型（single_choice / multiple_choice / fill_in / calculation）
        difficulty: 難度
        content: 題幹
        option_a/b/c/d: 選項
        correct_answer: 正解（多選用逗號）
        bloom_category: Bloom 認知層級
        figure_urls / figure_description: 題目附圖
        source_type: historical / ai / personal
        quality_flag / flag_reason: 品管標記
        retired_at / retention_reason: 退役時間與原因
        source_resource_id / owner_user_id: EPIC-035 個人題庫來源
        answer_source: authoritative / ai_inferred / user_confirmed
        confidence: AI 推論信心度
        needs_answer / never_for_scoring: 計分行為旗標
        tenant_id: 多租戶隔離鍵
    """

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=True,
        comment="使用者考試 FK（AI 生成題 / 模擬考）",
    )
    historical_exam_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("historical_exams.id", ondelete="CASCADE"), nullable=True,
        comment="歷史考試目錄 FK（爬蟲匯入的考古題）",
    )
    node_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="SET NULL")
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
    figure_urls: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}",
        comment="題目附圖路徑（相對或 URL）",
    )
    figure_description: Mapped[str | None] = mapped_column(
        Text, comment="圖片內容文字描述，供無法顯示圖時 fallback",
    )
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
        UUID(as_uuid=True), ForeignKey("knowledge_nodes.id", ondelete="SET NULL")
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="多租戶隔離鍵（NULL = 歸屬 public_b2c）",
        index=True,
    )
    # EPIC-035 fields
    source_resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="SET NULL"),
        comment="此題從哪份用戶資源抽出（NULL = 官方考古題或 AI 生成）",
    )
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        comment="個人題庫擁有者；NOT NULL 代表 scope=personal",
    )
    answer_source: Mapped[str | None] = mapped_column(
        String(20),
        comment="authoritative | ai_inferred | user_confirmed",
    )
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2))
    needs_answer: Mapped[bool] = mapped_column(Boolean, default=False)
    never_for_scoring: Mapped[bool] = mapped_column(Boolean, default=False)
    user_concept_note: Mapped[str | None] = mapped_column(Text)
    user_concept_note_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
