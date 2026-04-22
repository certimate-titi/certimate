"""ResourceParseJob ORM Model — EPIC-035 M6.

非同步解析任務紀錄，供後端追蹤 Gemini 解析狀態、成本、耗時。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ParseJobStatus(str, enum.Enum):
    QUEUED = "queued"
    PARSING = "parsing"
    SUCCESS = "success"
    FAILED = "failed"


class ResourceParseJob(Base):
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
