"""ImportTaskService — Manage async exam import job lifecycle (Phase 3)."""

import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import ImportTask
from app.models.import_task import ImportTaskStatus
from app.services.base import BaseService


class ImportTaskService(BaseService):
    """Manage async import task lifecycle (create, start, progress, complete, fail, cancel)."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        super().__init__(db)

    def create_import_task(
        self,
        user_id: uuid.UUID,
        exam_code: str,
        category_code: str,
        subject_code: str,
        exam_name: Optional[str] = None,
        question_pdf_path: Optional[str] = None,
        answer_pdf_path: Optional[str] = None,
        pdf_file_size: Optional[int] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """Create new import task and return task details.

        Args:
            user_id: User performing import
            exam_code: Exam code (e.g., 'P')
            category_code: Category code (e.g., '01')
            subject_code: Subject code (e.g., '0101')
            exam_name: Optional exam name
            question_pdf_path: Path to question PDF
            answer_pdf_path: Path to answer PDF
            pdf_file_size: Total file size in bytes
            tenant_id: Optional tenant ID for multi-tenancy

        Returns:
            {"task_id": uuid, "status": "pending", "created_at": datetime}
        """
        try:
            task = ImportTask(
                user_id=user_id,
                exam_code=exam_code,
                category_code=category_code,
                subject_code=subject_code,
                exam_name=exam_name,
                status=ImportTaskStatus.PENDING,
                question_pdf_path=question_pdf_path,
                answer_pdf_path=answer_pdf_path,
                pdf_file_size=pdf_file_size,
                tenant_id=tenant_id,
                progress_percent=0,
                quality_gates_passed=False,
                requires_manual_review=False,
                retry_count=0,
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)

            return self.ok(
                {
                    "task_id": str(task.id),
                    "status": task.status,
                    "created_at": task.created_at,
                }
            )
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to create import task: {str(e)}", 400)

    def get_task_status(self, task_id: uuid.UUID) -> dict:
        """Get current status of import task.

        Args:
            task_id: Task ID

        Returns:
            Task details including status, progress, errors
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            return self.ok(
                {
                    "task_id": str(task.id),
                    "status": task.status,
                    "exam_code": task.exam_code,
                    "category_code": task.category_code,
                    "subject_code": task.subject_code,
                    "progress_percent": task.progress_percent,
                    "total_questions": task.total_questions,
                    "questions_processed": task.questions_processed,
                    "questions_valid": task.questions_valid,
                    "questions_invalid": task.questions_invalid,
                    "questions_imported": task.questions_imported,
                    "error_message": task.error_message,
                    "validation_errors": task.validation_errors,
                    "import_errors": task.import_errors,
                    "quality_gates_passed": task.quality_gates_passed,
                    "requires_manual_review": task.requires_manual_review,
                    "retry_count": task.retry_count,
                    "created_at": task.created_at,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "cancelled_at": task.cancelled_at,
                    "historical_exam_id": str(task.historical_exam_id) if task.historical_exam_id else None,
                }
            )
        except Exception as e:
            return self.error(f"Failed to fetch task status: {str(e)}", 500)

    def start_processing(self, task_id: uuid.UUID) -> dict:
        """Mark task as PROCESSING and set started_at timestamp.

        Args:
            task_id: Task ID

        Returns:
            Updated task status
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            if task.status != ImportTaskStatus.PENDING:
                return self.error(f"Task cannot start from {task.status} status", 400)

            task.status = ImportTaskStatus.PROCESSING
            task.started_at = datetime.utcnow()
            task.progress_percent = 5
            self.db.commit()

            return self.ok({"status": task.status, "started_at": task.started_at})
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to start processing: {str(e)}", 500)

    def update_progress(
        self,
        task_id: uuid.UUID,
        processed: int,
        valid: int,
        invalid: int,
        progress_percent: int,
    ) -> dict:
        """Update import progress counters.

        Args:
            task_id: Task ID
            processed: Number of questions processed
            valid: Number of valid questions
            invalid: Number of invalid questions
            progress_percent: Overall progress percentage (0-100)

        Returns:
            Updated progress
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            task.questions_processed = processed
            task.questions_valid = valid
            task.questions_invalid = invalid
            task.progress_percent = min(progress_percent, 95)  # Cap at 95% until completion
            self.db.commit()

            return self.ok({"progress_percent": task.progress_percent})
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to update progress: {str(e)}", 500)

    def mark_validating(self, task_id: uuid.UUID, total_questions: int) -> dict:
        """Transition task to VALIDATING phase.

        Args:
            task_id: Task ID
            total_questions: Total questions found

        Returns:
            Updated status
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            task.status = ImportTaskStatus.VALIDATING
            task.total_questions = total_questions
            task.progress_percent = 25
            self.db.commit()

            return self.ok({"status": task.status})
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to mark validating: {str(e)}", 500)

    def mark_importing(self, task_id: uuid.UUID) -> dict:
        """Transition task to IMPORTING phase.

        Args:
            task_id: Task ID

        Returns:
            Updated status
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            task.status = ImportTaskStatus.IMPORTING
            task.progress_percent = 50
            self.db.commit()

            return self.ok({"status": task.status})
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to mark importing: {str(e)}", 500)

    def mark_completed(
        self,
        task_id: uuid.UUID,
        questions_imported: int,
        historical_exam_id: uuid.UUID,
        quality_gates_passed: bool = True,
    ) -> dict:
        """Mark task as COMPLETED with final counts.

        Args:
            task_id: Task ID
            questions_imported: Number of questions successfully imported
            historical_exam_id: ID of created HistoricalExam
            quality_gates_passed: Whether quality gates were passed

        Returns:
            Completion details
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            task.status = ImportTaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.questions_imported = questions_imported
            task.historical_exam_id = historical_exam_id
            task.quality_gates_passed = quality_gates_passed
            task.progress_percent = 100
            task.error_message = None
            self.db.commit()

            # Spec 26 §自動觸發考綱逆向工程
            # 考古題匯入完成 → 對對應 Subject 觸發 reverse engineering（從題目反推知識樹）
            # 失敗不阻擋 import 流程；admin endpoint 僅作為 monitoring/override
            self._trigger_reverse_engineering_safe(historical_exam_id)

            return self.ok(
                {
                    "status": task.status,
                    "completed_at": task.completed_at,
                    "questions_imported": questions_imported,
                }
            )
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to mark completed: {str(e)}", 500)

    def _trigger_reverse_engineering_safe(
        self, historical_exam_id: Optional[uuid.UUID]
    ) -> None:
        """Spec 26 §考古題匯入完成 → 自動觸發考綱逆向工程。

        從 historical_exam 找對應 Subject（透過 subject_code → exam_subject_codes
        或 subject_name 匹配），再呼叫 ReverseEngineeringService.extract。
        失敗只 log warning，不影響匯入交易。
        """
        if not historical_exam_id:
            return
        try:
            import logging
            from app.models.historical_exam import HistoricalExam
            from app.models.subject import Subject
            from app.services.reverse_engineering_service import (
                ReverseEngineeringService,
            )

            logger = logging.getLogger(__name__)
            he = self.db.query(HistoricalExam).filter_by(id=historical_exam_id).first()
            if not he:
                return

            # 找對應 Subject：優先用 subject_code 比對 exam_subject_codes（JSON list）
            subject = None
            if he.subject_code:
                subjects = self.db.query(Subject).all()
                for s in subjects:
                    codes = s.exam_subject_codes or []
                    if any(he.subject_code in str(c) for c in codes):
                        subject = s
                        break
            if not subject and he.subject_name:
                subject = self.db.query(Subject).filter_by(name=he.subject_name).first()

            if not subject:
                logger.info(
                    "Reverse engineering skipped: no Subject matched for "
                    "historical_exam %s (subject_code=%s, subject_name=%s)",
                    historical_exam_id, he.subject_code, he.subject_name,
                )
                return

            # 取觸發者 user_id（從 ImportTask 找回 admin）
            task = self.db.query(ImportTask).filter(
                ImportTask.historical_exam_id == historical_exam_id
            ).first()
            triggered_by = str(task.user_id) if task and task.user_id else None
            if not triggered_by:
                logger.info(
                    "Reverse engineering skipped: no triggered_by user for "
                    "historical_exam %s",
                    historical_exam_id,
                )
                return

            re_service = ReverseEngineeringService(self.db)
            # trigger() 會自己驗 admin 權限 + 題庫數量檢查
            result = re_service.trigger(triggered_by, str(subject.id))
            if result.get("error"):
                logger.warning(
                    "Reverse engineering trigger failed for subject %s: %s",
                    subject.id, result.get("message"),
                )
            else:
                logger.info(
                    "Auto reverse engineering triggered for subject %s after "
                    "historical_exam %s import",
                    subject.id, historical_exam_id,
                )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                "Reverse engineering auto-trigger crashed (non-blocking): %s", e,
            )

    def mark_failed(
        self,
        task_id: uuid.UUID,
        error_message: str,
        validation_errors: Optional[str] = None,
        import_errors: Optional[str] = None,
    ) -> dict:
        """Mark task as FAILED with error details.

        Args:
            task_id: Task ID
            error_message: Primary error message
            validation_errors: JSON-serialized validation errors
            import_errors: JSON-serialized import errors

        Returns:
            Failure details
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            task.status = ImportTaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = error_message
            task.validation_errors = validation_errors
            task.import_errors = import_errors
            self.db.commit()

            return self.ok(
                {
                    "status": task.status,
                    "error_message": error_message,
                    "completed_at": task.completed_at,
                }
            )
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to mark as failed: {str(e)}", 500)

    def mark_cancelled(self, task_id: uuid.UUID) -> dict:
        """Mark task as CANCELLED by user.

        Args:
            task_id: Task ID

        Returns:
            Cancellation details
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            if task.status == ImportTaskStatus.COMPLETED or task.status == ImportTaskStatus.FAILED:
                return self.error(f"Cannot cancel {task.status} task", 400)

            task.status = ImportTaskStatus.CANCELLED
            task.cancelled_at = datetime.utcnow()
            self.db.commit()

            return self.ok(
                {
                    "status": task.status,
                    "cancelled_at": task.cancelled_at,
                }
            )
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to cancel task: {str(e)}", 500)

    def list_user_tasks(
        self,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> dict:
        """List all import tasks for a user.

        Args:
            user_id: User ID
            limit: Page size
            offset: Page offset
            status_filter: Optional status filter (e.g., 'pending', 'completed', 'failed')

        Returns:
            Paginated task list
        """
        try:
            query = self.db.query(ImportTask).filter(ImportTask.user_id == user_id)

            if status_filter:
                query = query.filter(ImportTask.status == status_filter)

            total = query.count()
            tasks = query.order_by(ImportTask.created_at.desc()).offset(offset).limit(limit).all()

            task_list = [
                {
                    "task_id": str(task.id),
                    "exam_code": task.exam_code,
                    "category_code": task.category_code,
                    "subject_code": task.subject_code,
                    "status": task.status,
                    "progress_percent": task.progress_percent,
                    "questions_imported": task.questions_imported,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                }
                for task in tasks
            ]

            return self.ok(
                {
                    "tasks": task_list,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            )
        except Exception as e:
            return self.error(f"Failed to list tasks: {str(e)}", 500)

    def increment_retry_count(self, task_id: uuid.UUID) -> dict:
        """Increment retry counter for failed task.

        Args:
            task_id: Task ID

        Returns:
            Updated retry count
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            if task.retry_count >= 3:
                return self.error("Maximum retry attempts (3) exceeded", 400)

            task.retry_count += 1
            # Reset to pending for retry
            task.status = ImportTaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            task.cancelled_at = None
            task.progress_percent = 0
            self.db.commit()

            return self.ok(
                {
                    "retry_count": task.retry_count,
                    "status": task.status,
                }
            )
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to increment retry: {str(e)}", 500)

    def set_manual_review(self, task_id: uuid.UUID, note: Optional[str] = None) -> dict:
        """Mark task as requiring manual review (quality gates failed).

        Args:
            task_id: Task ID
            note: Optional review notes

        Returns:
            Update confirmation
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == task_id).first()
            if not task:
                return self.error("Task not found", 404)

            task.requires_manual_review = True
            task.quality_gates_passed = False
            if note:
                task.notes = note
            self.db.commit()

            return self.ok(
                {
                    "requires_manual_review": True,
                    "notes": task.notes,
                }
            )
        except Exception as e:
            self.db.rollback()
            return self.error(f"Failed to set manual review: {str(e)}", 500)
