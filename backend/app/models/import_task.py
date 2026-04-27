"""ImportTask ORM Model — Phase 3 async processing"""

import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, Enum, String, Text, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


class ImportTaskStatus(str, enum.Enum):
    """Status of an import task."""
    PENDING = "pending"           # Created, waiting to process
    PROCESSING = "processing"     # Currently extracting/validating
    VALIDATING = "validating"     # Validation gates running
    IMPORTING = "importing"       # Writing to database
    COMPLETED = "completed"       # Successfully completed
    FAILED = "failed"              # Failed at some stage
    CANCELLED = "cancelled"        # User cancelled


class ImportTask(Base):
    """考古題非同步匯入任務（Phase 3 async pipeline）。

    對應 DBML 表：import_tasks
    一條任務涵蓋 PDF 抽取 → 驗證 → 寫入 questions 三階段。

    Attributes:
        exam_code / category_code / subject_code: 試卷座標
        status: ImportTaskStatus（pending / processing / validating / importing /
            completed / failed / cancelled）
        total_questions / questions_processed / questions_valid /
            questions_invalid / questions_imported: 進度計數
        progress_percent: 0-100 百分比
        historical_exam_id: 匯入成功後對應的 historical_exams.id
        question_pdf_path / answer_pdf_path: 來源 PDF 路徑
        user_id / tenant_id: 觸發者與多租戶隔離鍵
        quality_gates_passed / requires_manual_review: 驗證閘門結果
        retry_count: 失敗重試次數
    """

    __tablename__ = "import_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Exam identifiers
    exam_code: Mapped[str] = mapped_column(String(50), nullable=False)
    category_code: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_code: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_name: Mapped[str | None] = mapped_column(String(255))

    # Task status
    status: Mapped[str] = mapped_column(
        Enum(ImportTaskStatus, name="import_task_status", create_type=False,
             values_callable=lambda e: [m.value for m in e]),
        default=ImportTaskStatus.PENDING,
        nullable=False,
    )

    # Progress tracking
    total_questions: Mapped[int | None] = mapped_column(Integer)
    questions_processed: Mapped[int] = mapped_column(Integer, default=0)
    questions_valid: Mapped[int] = mapped_column(Integer, default=0)
    questions_invalid: Mapped[int] = mapped_column(Integer, default=0)
    questions_imported: Mapped[int] = mapped_column(Integer, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Results
    validation_errors: Mapped[str | None] = mapped_column(Text)
    import_errors: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    historical_exam_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="FK to historical_exams after successful import"
    )

    # File tracking
    question_pdf_path: Mapped[str | None] = mapped_column(String(500))
    answer_pdf_path: Mapped[str | None] = mapped_column(String(500))
    pdf_file_size: Mapped[int | None] = mapped_column(Integer)

    # User & tenant
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Metadata
    quality_gates_passed: Mapped[bool] = mapped_column(default=False)
    requires_manual_review: Mapped[bool] = mapped_column(default=False)
    retry_count: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text)

    def __repr__(self):
        """除錯用簡短表示。

        Returns:
            str: 包含試卷座標、status、progress 的字串
        """
        return (
            f"<ImportTask {self.exam_code}/{self.category_code}/{self.subject_code} "
            f"status={self.status} progress={self.progress_percent}%>"
        )
