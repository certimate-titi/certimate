"""ResourceScaffold ORM Model — EPIC-035 M7 學習鷹架 Layer A.

章節級重點提煉（takeaway）/ 延遲思考題（elaborative）/ 策略提示（strategy）。
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class ResourceScaffoldType(str, enum.Enum):
    TAKEAWAY = "takeaway"
    ELABORATIVE = "elaborative"
    STRATEGY = "strategy"


class ResourceScaffold(Base):
    __tablename__ = "resource_scaffolds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
