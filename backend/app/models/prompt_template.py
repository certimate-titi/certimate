"""PromptTemplate ORM Models — Prompt 模板管理 (Feature 30).

新版架構（v2）：
  - prompt_templates_v2: 模板主表（取代舊 prompt_templates）
  - prompt_template_versions: 版本歷史（取代舊 prompt_template_history）
  - prompt_ab_tests: A/B 測試表（新增）

舊版模型（PromptTemplate / PromptTemplateHistory）保留以供 Migration 011 向下相容。
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


# ──────────────────────────────────────────────
# 舊版 (v1) — 保留以供向下相容
# ──────────────────────────────────────────────

class PromptStageStatus(str, enum.Enum):
    """舊版 Prompt 階段啟用狀態列舉。"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class PromptTemplate(Base):
    """舊版 Prompt 模板（已被 PromptTemplateV2 取代）。"""
    __tablename__ = "prompt_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    stage_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stage_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(PromptStageStatus, name="prompt_stage_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=PromptStageStatus.ACTIVE,
    )
    content: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    modified_by: Mapped[Optional[str]] = mapped_column(String(255))
    modified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PromptTemplateHistory(Base):
    """舊版版本歷史（已被 PromptTemplateVersion 取代）。"""
    __tablename__ = "prompt_template_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    modified_by: Mapped[Optional[str]] = mapped_column(String(255))
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# ──────────────────────────────────────────────
# 新版 (v2) — Feature 30 DBML SSOT
# ──────────────────────────────────────────────

class PromptCategory(str, enum.Enum):
    """Prompt 模板分類列舉（safety / knowledge / exam / teaching / emotion）。"""

    SAFETY = "safety"
    KNOWLEDGE = "knowledge"
    EXAM = "exam"
    TEACHING = "teaching"
    EMOTION = "emotion"


class AbTestStatus(str, enum.Enum):
    """Prompt A/B 測試狀態列舉。"""

    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PromptTemplateV2(Base):
    """Prompt 模板主表 — 存放當前生效版本。

    SSOT: project/specs/entity/erm.dbml -> Table prompt_templates (v2)
    """

    __tablename__ = "prompt_templates_v2"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False,
        comment="e.g. S-01, K-01, T-02"
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
        comment="英文識別名 e.g. safety_router"
    )
    display_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment="中文顯示名 e.g. 三維度安全分類"
    )
    category: Mapped[str] = mapped_column(
        Enum(PromptCategory, name="prompt_category", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="gemini-flash / claude-3.5-sonnet / vision / by-plan"
    )
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    max_tokens_by_plan: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        comment='{"PRO_199":1024,"PRO_PLUS_399":2048,"ULTRA_1599":4096}'
    )
    temperature: Mapped[float] = mapped_column(
        Numeric(2, 1), nullable=False, default=0.5
    )
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list,
        comment='[{"name":"subject_name","description":"...","example":"..."}]'
    )
    feature_refs: Mapped[Optional[list]] = mapped_column(
        ARRAY(Text), default=list,
        comment="關聯的 Feature 檔案"
    )
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PromptTemplateVersion(Base):
    """Prompt 版本歷史 — Append-only, immutable.

    SSOT: project/specs/entity/erm.dbml -> Table prompt_template_versions
    """

    __tablename__ = "prompt_template_versions"

    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uq_ptv_template_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    max_tokens_by_plan: Mapped[Optional[dict]] = mapped_column(JSONB)
    temperature: Mapped[float] = mapped_column(Numeric(2, 1), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    change_note: Mapped[Optional[str]] = mapped_column(
        Text, comment="版本變更說明"
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PromptAbTest(Base):
    """Prompt A/B 測試 — 同一模板最多一個 running 測試。

    SSOT: project/specs/entity/erm.dbml -> Table prompt_ab_tests
    """

    __tablename__ = "prompt_ab_tests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(
        String(200), nullable=False,
        comment='A/B 測試名稱 e.g. "教練語氣對比"'
    )
    variant_a_version: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="對照組版本號"
    )
    variant_b_system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    variant_b_user_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    variant_b_temperature: Mapped[Optional[float]] = mapped_column(Numeric(2, 1))
    traffic_split: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50,
        comment="variant B 流量百分比 (0-100)"
    )
    status: Mapped[str] = mapped_column(
        Enum(AbTestStatus, name="ab_test_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=AbTestStatus.RUNNING,
    )
    metric_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        comment="追蹤指標：accuracy / satisfaction / cost"
    )
    variant_a_metric_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4), comment="A 組指標值"
    )
    variant_b_metric_value: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 4), comment="B 組指標值"
    )
    winner: Mapped[Optional[str]] = mapped_column(
        String(1), comment="A / B / null (未決)"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
