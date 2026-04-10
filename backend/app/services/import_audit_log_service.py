"""ImportAuditLogService — Log and query import audit events (Phase 3)."""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.import_audit_log import ImportAuditLog, ImportAuditAction
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class ImportAuditLogService(BaseService):
    """Log and retrieve import audit trail."""

    def __init__(self, db: Session):
        """Initialize service with database session."""
        super().__init__(db)

    def log_event(
        self,
        import_task_id: uuid.UUID,
        action: str,
        user_id: uuid.UUID,
        exam_code: str,
        category_code: str,
        subject_code: str,
        status: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[dict] = None,
        questions_processed: Optional[int] = None,
        questions_valid: Optional[int] = None,
        questions_imported: Optional[int] = None,
        duration_ms: Optional[int] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        tenant_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """Log an import audit event.

        Args:
            import_task_id: Task UUID
            action: ImportAuditAction value
            user_id: User performing action
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            status: Event status (success/failed)
            message: Human-readable message
            details: Optional metadata dict (will be JSON serialized)
            questions_processed: Count of processed questions
            questions_valid: Count of valid questions
            questions_imported: Count of imported questions
            duration_ms: Duration of action in milliseconds
            error_code: Error code if failed
            error_message: Error message if failed
            tenant_id: Optional tenant ID

        Returns:
            Audit log entry details
        """
        try:
            # Serialize details dict to JSON
            details_json = json.dumps(details) if details else None

            log_entry = ImportAuditLog(
                import_task_id=import_task_id,
                action=action,
                user_id=user_id,
                exam_code=exam_code,
                category_code=category_code,
                subject_code=subject_code,
                tenant_id=tenant_id,
                status=status,
                message=message,
                details=details_json,
                questions_processed=questions_processed,
                questions_valid=questions_valid,
                questions_imported=questions_imported,
                duration_ms=duration_ms,
                error_code=error_code,
                error_message=error_message,
            )
            self.db.add(log_entry)
            self.db.commit()
            self.db.refresh(log_entry)

            logger.info(
                f"Logged audit event: task={import_task_id}, action={action}, "
                f"exam={exam_code}/{category_code}/{subject_code}, status={status}"
            )

            return self.ok({
                "log_id": str(log_entry.id),
                "action": log_entry.action,
                "status": log_entry.status,
                "created_at": log_entry.created_at,
            })

        except Exception as e:
            self.db.rollback()
            logger.exception(f"Failed to log audit event: {str(e)}")
            return self.error(500, f"Failed to log event: {str(e)}")

    def get_task_audit_trail(
        self,
        import_task_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get complete audit trail for a task.

        Args:
            import_task_id: Task UUID
            limit: Max entries to return
            offset: Page offset

        Returns:
            Paginated audit log entries
        """
        try:
            query = self.db.query(ImportAuditLog).filter(
                ImportAuditLog.import_task_id == import_task_id
            )

            total = query.count()
            entries = (
                query.order_by(ImportAuditLog.created_at.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            audit_trail = [
                {
                    "log_id": str(entry.id),
                    "action": entry.action,
                    "status": entry.status,
                    "message": entry.message,
                    "details": json.loads(entry.details) if entry.details else None,
                    "questions_processed": entry.questions_processed,
                    "questions_valid": entry.questions_valid,
                    "questions_imported": entry.questions_imported,
                    "duration_ms": entry.duration_ms,
                    "error_code": entry.error_code,
                    "error_message": entry.error_message,
                    "created_at": entry.created_at,
                }
                for entry in entries
            ]

            return self.ok({
                "audit_trail": audit_trail,
                "total": total,
                "limit": limit,
                "offset": offset,
            })

        except Exception as e:
            logger.exception(f"Failed to get audit trail: {str(e)}")
            return self.error(500, f"Failed to retrieve audit trail: {str(e)}")

    def get_user_audit_logs(
        self,
        user_id: uuid.UUID,
        action_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Get audit logs for a user's import activities.

        Args:
            user_id: User UUID
            action_filter: Optional action filter
            limit: Max entries
            offset: Page offset

        Returns:
            Paginated audit logs for user
        """
        try:
            query = self.db.query(ImportAuditLog).filter(ImportAuditLog.user_id == user_id)

            if action_filter:
                query = query.filter(ImportAuditLog.action == action_filter)

            total = query.count()
            entries = (
                query.order_by(ImportAuditLog.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            logs = [
                {
                    "log_id": str(entry.id),
                    "task_id": str(entry.import_task_id),
                    "action": entry.action,
                    "exam_code": entry.exam_code,
                    "category_code": entry.category_code,
                    "subject_code": entry.subject_code,
                    "status": entry.status,
                    "message": entry.message,
                    "questions_imported": entry.questions_imported,
                    "created_at": entry.created_at,
                }
                for entry in entries
            ]

            return self.ok({
                "logs": logs,
                "total": total,
                "limit": limit,
                "offset": offset,
            })

        except Exception as e:
            logger.exception(f"Failed to get user audit logs: {str(e)}")
            return self.error(500, f"Failed to retrieve logs: {str(e)}")

    def get_import_statistics(self) -> dict:
        """Get aggregate import statistics from audit logs.

        Returns:
            Statistics including total imports, success rate, average duration
        """
        try:
            total_tasks = (
                self.db.query(ImportAuditLog)
                .filter(ImportAuditLog.action == ImportAuditAction.TASK_CREATED.value)
                .count()
            )

            successful = (
                self.db.query(ImportAuditLog)
                .filter(ImportAuditLog.action == ImportAuditAction.TASK_COMPLETED.value)
                .count()
            )

            failed = (
                self.db.query(ImportAuditLog)
                .filter(ImportAuditLog.action == ImportAuditAction.TASK_FAILED.value)
                .count()
            )

            cancelled = (
                self.db.query(ImportAuditLog)
                .filter(ImportAuditLog.action == ImportAuditAction.TASK_CANCELLED.value)
                .count()
            )

            # Calculate average duration for completed tasks
            completed_logs = self.db.query(ImportAuditLog).filter(
                ImportAuditLog.action == ImportAuditAction.TASK_COMPLETED.value
            ).all()

            avg_duration = 0
            if completed_logs:
                durations = [log.duration_ms for log in completed_logs if log.duration_ms]
                if durations:
                    avg_duration = sum(durations) / len(durations)

            success_rate = (successful / total_tasks * 100) if total_tasks > 0 else 0

            # Total questions imported
            total_questions = (
                self.db.query(ImportAuditLog)
                .filter(ImportAuditLog.action == ImportAuditAction.TASK_COMPLETED.value)
                .with_entities(ImportAuditLog.questions_imported)
                .all()
            )
            total_imported = sum([q[0] for q in total_questions if q[0]])

            return self.ok({
                "total_tasks": total_tasks,
                "successful": successful,
                "failed": failed,
                "cancelled": cancelled,
                "success_rate": round(success_rate, 2),
                "average_duration_ms": round(avg_duration, 0),
                "total_questions_imported": total_imported,
            })

        except Exception as e:
            logger.exception(f"Failed to compute statistics: {str(e)}")
            return self.error(500, f"Failed to compute statistics: {str(e)}")

    def search_audit_logs(
        self,
        exam_code: Optional[str] = None,
        status: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Search audit logs by various criteria.

        Args:
            exam_code: Filter by exam code
            status: Filter by status (success/failed)
            action: Filter by action type
            limit: Max results
            offset: Page offset

        Returns:
            Filtered audit logs
        """
        try:
            query = self.db.query(ImportAuditLog)

            if exam_code:
                query = query.filter(ImportAuditLog.exam_code == exam_code)
            if status:
                query = query.filter(ImportAuditLog.status == status)
            if action:
                query = query.filter(ImportAuditLog.action == action)

            total = query.count()
            entries = (
                query.order_by(ImportAuditLog.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            results = [
                {
                    "log_id": str(entry.id),
                    "task_id": str(entry.import_task_id),
                    "action": entry.action,
                    "exam": f"{entry.exam_code}/{entry.category_code}/{entry.subject_code}",
                    "status": entry.status,
                    "message": entry.message,
                    "questions_imported": entry.questions_imported,
                    "duration_ms": entry.duration_ms,
                    "created_at": entry.created_at,
                }
                for entry in entries
            ]

            return self.ok({
                "results": results,
                "total": total,
                "limit": limit,
                "offset": offset,
            })

        except Exception as e:
            logger.exception(f"Failed to search audit logs: {str(e)}")
            return self.error(500, f"Failed to search logs: {str(e)}")
