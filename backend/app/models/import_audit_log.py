"""ImportAuditLog ORM Model — Track all import events (Phase 3)."""

import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, String, Text, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


class ImportAuditAction(str, enum.Enum):
    """Type of import audit event."""
    TASK_CREATED = "task_created"           # Import task created
    TASK_STARTED = "task_started"           # Processing began
    EXTRACTION_STARTED = "extraction_started"  # PDF extraction started
    EXTRACTION_COMPLETE = "extraction_complete"  # PDF extraction done
    VALIDATION_STARTED = "validation_started"  # Validation gates running
    VALIDATION_COMPLETE = "validation_complete"  # Validation finished
    IMPORT_STARTED = "import_started"       # Database import started
    IMPORT_COMPLETE = "import_complete"     # Database import done
    QUALITY_GATES_PASSED = "quality_gates_passed"  # All quality checks passed
    QUALITY_GATES_FAILED = "quality_gates_failed"  # Quality checks failed
    MANUAL_REVIEW_REQUIRED = "manual_review_required"  # Flagged for review
    TASK_COMPLETED = "task_completed"       # Task finished successfully
    TASK_FAILED = "task_failed"             # Task failed
    TASK_CANCELLED = "task_cancelled"       # Task cancelled by user
    TASK_RETRIED = "task_retried"          # Failed task retried
    IMPORT_ROLLED_BACK = "import_rolled_back"  # Import undone


class ImportAuditLog(Base):
    """Audit trail for all import operations."""
    __tablename__ = "import_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Task reference
    import_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
        comment="FK to import_tasks"
    )

    # Event details
    action: Mapped[str] = mapped_column(
        Enum(ImportAuditAction, name="import_audit_action", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        index=True,
    )

    # User/tenant context
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Exam identifiers
    exam_code: Mapped[str] = mapped_column(String(50), nullable=False)
    category_code: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_code: Mapped[str] = mapped_column(String(100), nullable=False)

    # Action details
    status: Mapped[str | None] = mapped_column(String(50))  # e.g., "success", "failed"
    message: Mapped[str | None] = mapped_column(Text)  # Human-readable message
    details: Mapped[str | None] = mapped_column(Text)  # JSON metadata

    # Results snapshot
    questions_processed: Mapped[int | None] = mapped_column(Integer)
    questions_valid: Mapped[int | None] = mapped_column(Integer)
    questions_imported: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)  # How long this action took

    # Error tracking
    error_code: Mapped[str | None] = mapped_column(String(50))
    error_message: Mapped[str | None] = mapped_column(Text)

    # Timeline
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self):
        return (
            f"<ImportAuditLog {self.exam_code}/{self.category_code}/{self.subject_code} "
            f"action={self.action} status={self.status}>"
        )
