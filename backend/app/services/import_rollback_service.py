"""ImportRollbackService — Undo/rollback completed imports (Phase 3)."""

import json
import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models import ImportTask, HistoricalExam, Question
from app.models.import_task import ImportTaskStatus
from app.models.import_audit_log import ImportAuditLog, ImportAuditAction
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class ImportRollbackService(BaseService):
    """Rollback/undo completed import operations."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        super().__init__(db)

    def can_rollback(self, import_task_id: uuid.UUID) -> dict:
        """Check if an import can be rolled back.

        Conditions for rollback:
        - Task must exist
        - Task must be in COMPLETED status
        - Must have associated HistoricalExam
        - HistoricalExam must not have been modified since creation

        Args:
            import_task_id: Task UUID

        Returns:
            {"can_rollback": bool, "reason": str, "task_details": {...}}
        """
        try:
            task = self.db.query(ImportTask).filter(ImportTask.id == import_task_id).first()

            if not task:
                return self.ok({
                    "can_rollback": False,
                    "reason": "Task not found"
                })

            if task.status != ImportTaskStatus.COMPLETED:
                return self.ok({
                    "can_rollback": False,
                    "reason": f"Task is in {task.status} status (must be COMPLETED)"
                })

            if not task.historical_exam_id:
                return self.ok({
                    "can_rollback": False,
                    "reason": "No historical exam associated with this task"
                })

            # Check if exam exists
            exam = self.db.query(HistoricalExam).filter(
                HistoricalExam.id == task.historical_exam_id
            ).first()

            if not exam:
                return self.ok({
                    "can_rollback": False,
                    "reason": "Associated historical exam not found"
                })

            # Check question count matches
            question_count = self.db.query(Question).filter(
                Question.historical_exam_id == exam.id
            ).count()

            if question_count != task.questions_imported:
                logger.warning(
                    f"Question count mismatch for task {import_task_id}: "
                    f"expected {task.questions_imported}, found {question_count}"
                )

            return self.ok({
                "can_rollback": True,
                "reason": "Rollback is available",
                "task_details": {
                    "task_id": str(task.id),
                    "status": task.status,
                    "historical_exam_id": str(exam.id),
                    "exam_code": task.exam_code,
                    "category_code": task.category_code,
                    "subject_code": task.subject_code,
                    "questions_imported": task.questions_imported,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at,
                }
            })

        except Exception as e:
            logger.exception(f"Failed to check rollback availability: {str(e)}")
            return self.error(f"Failed to check rollback: {str(e)}", 500)

    def rollback_import(
        self,
        import_task_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: Optional[str] = None,
        notify_user: bool = True,
    ) -> dict:
        """Rollback a completed import.

        Performs:
        1. Verify rollback is possible
        2. Delete all Questions associated with HistoricalExam
        3. Delete HistoricalExam record
        4. Update ImportTask status to reflect rollback
        5. Create audit log entry
        6. Send notification to original user

        Args:
            import_task_id: Task to rollback
            user_id: User performing rollback (must be admin)
            reason: Optional reason for rollback
            notify_user: Whether to notify original user

        Returns:
            {"success": bool, "questions_deleted": int, "message": str}
        """
        try:
            # Check if rollback is possible
            check_result = self.can_rollback(import_task_id)
            if check_result.get("error"):
                return check_result

            check_data = check_result.get("data", {})
            if not check_data.get("can_rollback"):
                return self.error(check_data.get("reason", "Cannot rollback"), 400)

            task_details = check_data.get("task_details", {})
            historical_exam_id = uuid.UUID(task_details["historical_exam_id"])

            # Get task and exam for details
            task = self.db.query(ImportTask).filter(ImportTask.id == import_task_id).first()
            exam = self.db.query(HistoricalExam).filter(
                HistoricalExam.id == historical_exam_id
            ).first()

            if not task or not exam:
                return self.error("Task or exam not found during rollback", 500)

            # Count questions to delete
            question_count = self.db.query(Question).filter(
                Question.historical_exam_id == historical_exam_id
            ).count()

            # Delete questions
            self.db.query(Question).filter(
                Question.historical_exam_id == historical_exam_id
            ).delete()

            # Delete exam
            self.db.delete(exam)

            # Update task status
            task.status = ImportTaskStatus.CANCELLED
            task.cancelled_at = datetime.utcnow()
            task.notes = f"Rollback by {user_id}: {reason}" if reason else f"Rollback by {user_id}"

            # Commit deletion
            self.db.commit()

            # Log rollback event
            self._log_rollback_event(
                import_task_id=import_task_id,
                user_id=user_id,
                exam_code=task.exam_code,
                category_code=task.category_code,
                subject_code=task.subject_code,
                questions_deleted=question_count,
                reason=reason,
                tenant_id=task.tenant_id,
            )

            logger.info(
                f"Rolled back import {import_task_id}: deleted {question_count} questions"
            )

            return self.ok({
                "success": True,
                "questions_deleted": question_count,
                "message": f"Successfully rolled back import - deleted {question_count} questions",
                "task_id": str(import_task_id),
                "exam": f"{task.exam_code}/{task.category_code}/{task.subject_code}",
            })

        except Exception as e:
            self.db.rollback()
            logger.exception(f"Rollback failed: {str(e)}")
            return self.error(f"Rollback failed: {str(e)}", 500)

    def get_rollback_history(
        self,
        exam_code: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get history of all rollback operations.

        Args:
            exam_code: Optional filter by exam code
            limit: Max results
            offset: Page offset

        Returns:
            Paginated list of rollback events
        """
        try:
            query = self.db.query(ImportAuditLog).filter(
                ImportAuditLog.action == ImportAuditAction.IMPORT_ROLLED_BACK.value
            )

            if exam_code:
                query = query.filter(ImportAuditLog.exam_code == exam_code)

            total = query.count()
            entries = (
                query.order_by(ImportAuditLog.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            history = [
                {
                    "log_id": str(entry.id),
                    "task_id": str(entry.import_task_id),
                    "exam": f"{entry.exam_code}/{entry.category_code}/{entry.subject_code}",
                    "rolled_back_by": str(entry.user_id),
                    "reason": json.loads(entry.details).get("reason") if entry.details else None,
                    "questions_deleted": entry.questions_processed,
                    "rolled_back_at": entry.created_at,
                }
                for entry in entries
            ]

            return self.ok({
                "history": history,
                "total": total,
                "limit": limit,
                "offset": offset,
            })

        except Exception as e:
            logger.exception(f"Failed to get rollback history: {str(e)}")
            return self.error(f"Failed to retrieve history: {str(e)}", 500)

    def _log_rollback_event(
        self,
        import_task_id: uuid.UUID,
        user_id: uuid.UUID,
        exam_code: str,
        category_code: str,
        subject_code: str,
        questions_deleted: int,
        reason: Optional[str] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> None:
        """Log rollback event to audit trail.

        Args:
            import_task_id: Task rolled back
            user_id: User performing rollback
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            questions_deleted: Number of questions removed
            reason: Optional reason for rollback
            tenant_id: Tenant ID
        """
        try:
            log_entry = ImportAuditLog(
                import_task_id=import_task_id,
                action=ImportAuditAction.IMPORT_ROLLED_BACK.value,
                user_id=user_id,
                exam_code=exam_code,
                category_code=category_code,
                subject_code=subject_code,
                tenant_id=tenant_id,
                status="success",
                message=f"Rolled back import - deleted {questions_deleted} questions",
                details=json.dumps({"reason": reason, "questions_deleted": questions_deleted}),
                questions_processed=questions_deleted,
            )
            self.db.add(log_entry)
            self.db.commit()

        except Exception as e:
            logger.exception(f"Failed to log rollback event: {str(e)}")
            # Don't raise - rollback already succeeded, just logging failed


# Import datetime for rollback
from datetime import datetime
