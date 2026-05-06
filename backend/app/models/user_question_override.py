"""UserQuestionOverride ORM Model — 使用者對特定題目的手動標記。

對應 DBML 表：user_question_overrides
PK: (user_id, question_id)；is_mastered=True 時題目從錯題本與錯題考試候選池移除。
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, func, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class UserQuestionOverride(Base):
    """使用者對題目的手動覆寫（目前僅支援 is_mastered）。"""

    __tablename__ = "user_question_overrides"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    is_mastered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "question_id", name="pk_user_question_overrides"),
    )
