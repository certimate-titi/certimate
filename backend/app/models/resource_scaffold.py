"""ResourceScaffold ORM Model — EPIC-035 M7 學習鷹架 Layer A.

章節級重點提煉（takeaway）/ 延遲思考題（elaborative）/ 策略提示（strategy）。
"""

import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ResourceScaffoldType(str, enum.Enum):
    """學習鷹架類型列舉（6 種）。

    - takeaway：章節重點精煉（含 retrieval_prompt，UX 摺疊式檢索觸發）
    - elaborative：延伸思考題
    - strategy：學習策略建議
    - pitfall：迷思警示（Sprint 2 P1 / migration 083）
      → 教學原理 Misconception Correction、紅色警示卡預設展開
    - advance_organizer：讀前定錨（Sprint 4 P3 / migration 084）
      → Ausubel Subsumption Theory，章節閱讀前先建立心智錨點
    - concept_extract：考古題核心概念（Sprint 4 P3 / migration 084）
      → K-06-quiz 解題後對照用，emerald 卡片
    """

    TAKEAWAY = "takeaway"
    ELABORATIVE = "elaborative"
    STRATEGY = "strategy"
    PITFALL = "pitfall"
    ADVANCE_ORGANIZER = "advance_organizer"
    CONCEPT_EXTRACT = "concept_extract"


class ResourceScaffold(Base):
    """章節級學習鷹架（重點提煉 / 延遲思考題 / 策略提示）。

    對應 DBML 表：resource_scaffolds
    EPIC-035 M7 Layer A；從屬於 Resource（CASCADE）。

    Attributes:
        resource_id: 來源資源
        tenant_id: 多租戶隔離鍵
        chapter_heading: 章節標題
        type: takeaway / elaborative / strategy
        content: 鷹架內容（題目或重點）
        user_response: 使用者作答（elaborative 用）
        responded_at: 作答時間
        page_start / page_end: 對應頁碼
        reference_answer: 參考答案
    """

    __tablename__ = "resource_scaffolds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=True,
        comment="來源資源（正式鷹架必填；AI 補洞鷹架 is_orphan_fill=True 時可為 NULL）",
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    chapter_heading: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(
        Enum(ResourceScaffoldType, name="resource_scaffold_type",
             create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_response: Mapped[str | None] = mapped_column(Text)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    page_start: Mapped[int | None] = mapped_column(Integer)
    page_end: Mapped[int | None] = mapped_column(Integer)
    reference_answer: Mapped[str | None] = mapped_column(Text)
    # P0 (Sprint 1 T02)：retrieval-first UX 必備
    retrieval_prompt: Mapped[str | None] = mapped_column(Text)
    template_code: Mapped[str | None] = mapped_column(String(32))
    # P6 (Sprint 7 T54)：1024 維 voyage embedding（給 /concept-center 語意搜尋用）
    embedding = mapped_column(Vector(1024), nullable=True)
    # Sprint 11 #2 AI 補洞鷹架（migration 093）
    trust_level: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        comment="HUMAN_VERIFIED / SYSTEM_GENERATED / AI_INFERRED / PENDING_REVIEW",
    )
    confidence_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="AI 補洞信心分數 0-100；正式鷹架為 NULL",
    )
    evidence_question_ids: Mapped[list[uuid.UUID] | None] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True,
        comment="佐證考古題 id 陣列（最多 8 題）",
    )
    is_orphan_fill: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="FALSE",
        default=False,
        comment="是否為 AI 補洞鷹架（K-ORPHAN-01 生成）",
    )
    generation_failure_reason: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="evidence_insufficient / semantic_drift / url_detected / llm_error",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
