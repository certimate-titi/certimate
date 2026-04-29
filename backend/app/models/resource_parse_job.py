"""ResourceParseJob ORM Model — EPIC-035 M6.

非同步解析任務紀錄，供後端追蹤 Gemini 解析狀態、成本、耗時。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ParseJobStatus(str, enum.Enum):
    """解析任務狀態列舉（queued / parsing / success / failed）。"""

    QUEUED = "queued"
    PARSING = "parsing"
    SUCCESS = "success"
    FAILED = "failed"


class ResourceParseJob(Base):
    """非同步資源解析任務（Gemini 多模態）。

    對應 DBML 表：resource_parse_jobs
    EPIC-035 M6；追蹤 Gemini 解析狀態、token 消耗與成本。

    Attributes:
        resource_id: 來源資源（CASCADE）
        tenant_id: 多租戶隔離鍵
        status: queued / parsing / success / failed
        gemini_model: 使用的 Gemini 模型 ID
        input_tokens / output_tokens / cost_usd: 用量與成本
        started_at / finished_at: 起訖時間
        failure_reason: 失敗原因（QA 空態判斷必查）
        critical_pages: 關鍵頁清單
        detected_content_type: 偵測內容型別
        checkpoint_data: Worker checkpoint 進度（schema: {last_completed_step, step_data}）
    """

    __tablename__ = "resource_parse_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(
        Enum(ParseJobStatus, name="parse_job_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=ParseJobStatus.QUEUED,
    )
    gemini_model: Mapped[str | None] = mapped_column(String(50))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 4))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    critical_pages: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, server_default="{}"
    )
    detected_content_type: Mapped[str | None] = mapped_column(String(30))
    checkpoint_data: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
