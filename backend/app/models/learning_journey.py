"""LearningJourney ORM Model — derived from erm.dbml."""

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class LearningMode(str, enum.Enum):
    """學習節奏列舉（衝刺 / 標準 / 精熟）。"""

    SPRINT = "sprint"
    STANDARD = "standard"
    MASTERY = "mastery"


class SelfAssessedLevel(str, enum.Enum):
    """使用者自評程度列舉。"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningJourney(Base):
    """使用者在某科目的學習旅程設定。

    對應 DBML 表：learning_journeys
    Unique（user_id, subject_id）；驅動 schedule、推薦等模組。

    Attributes:
        user_id: 學習者（CASCADE）
        subject_id: 所屬科目
        exam_date: 預定考試日
        result_date / exam_result_status: 結果日期與通過狀態
        data_expiry_date: 學習資料保留至何時
        self_assessed_level: 自評程度（beginner / intermediate / advanced）
        learning_mode: 節奏（sprint / standard / mastery）
        is_archived: 是否封存
    """

    __tablename__ = "learning_journeys"
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_learning_journeys_user_subject"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False
    )
    exam_date: Mapped[date | None] = mapped_column(Date)
    result_date: Mapped[date | None] = mapped_column(Date)
    exam_result_status: Mapped[str | None] = mapped_column(
        String(20)
    )
    data_expiry_date: Mapped[date | None] = mapped_column(Date)
    self_assessed_level: Mapped[str] = mapped_column(
        Enum(SelfAssessedLevel, name="self_assessed_level", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=SelfAssessedLevel.BEGINNER,
    )
    learning_mode: Mapped[str] = mapped_column(
        Enum(LearningMode, name="learning_mode", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=LearningMode.STANDARD,
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
