"""WeeklyReport ORM Model — derived from erm.dbml."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, Text, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from app.models import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "report_week", name="uq_weekly_reports_user_week"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    report_week: Mapped[date] = mapped_column(Date, nullable=False)
    study_hours: Mapped[float | None] = mapped_column(Numeric(5, 1))
    exams_completed: Mapped[int | None] = mapped_column(Integer)
    questions_answered: Mapped[int | None] = mapped_column(Integer)
    progress_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
