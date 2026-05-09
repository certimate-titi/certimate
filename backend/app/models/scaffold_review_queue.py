"""ScaffoldReviewQueue ORM Model — Sprint 11 #2 AI 補洞鷹架退出機制.

學生標記「不準確」後寫入此表；
≥ 3 份不同用戶回報 → 自動觸發鷹架隱藏流程。

對應 DBML 表：scaffold_review_queue
RLS 啟用：tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


VALID_REASON_CODES = frozenset({
    "definition_wrong",
    "example_wrong",
    "answer_wrong",
    "unrelated",
    "other",
})


class ScaffoldReviewQueue(Base):
    """AI 補洞鷹架不準確回報佇列。

    Attributes:
        scaffold_id: 被回報的鷹架 (CASCADE 刪除)
        reporter_user_id: 回報者（CASCADE 刪除）
        reason_code: definition_wrong / example_wrong / answer_wrong / unrelated / other
        note: 自由填寫說明（≤ 100 字）
        tenant_id: 多租戶隔離鍵（RLS）
        created_at: 回報時間
    """

    __tablename__ = "scaffold_review_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    scaffold_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource_scaffolds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reporter_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="definition_wrong / example_wrong / answer_wrong / unrelated / other",
    )
    note: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="自由填寫說明（限 100 字）",
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="多租戶隔離鍵（NULL = public_b2c）",
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
