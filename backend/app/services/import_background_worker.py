"""Background job worker for async exam imports using APScheduler (Phase 3)."""

import json
import logging
import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models import ImportTask, HistoricalExam
from app.services.import_task_service import ImportTaskService
from app.services.exam_pdf_extraction_service import ExamPDFExtractionService
from app.services.historical_exam_import_service import HistoricalExamImportService

logger = logging.getLogger(__name__)
settings = get_settings()


class ImportBackgroundWorker:
    """Process async import tasks from queue."""

    def __init__(self, db_session: Session):
        """Initialize worker with database session.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.task_service = ImportTaskService(db_session)
        self.extraction_service = ExamPDFExtractionService()
        self.import_service = HistoricalExamImportService(db_session)

    def process_import_task(self, task_id: str) -> dict:
        """Main entry point: Process a single import task end-to-end.

        Workflow:
        1. Load task from database
        2. Validate file paths exist
        3. Extract questions & answers from PDFs (Phase 1)
        4. Run validation gates
        5. Mark for quality review if needed
        6. Import to database (Phase 2)
        7. Update task status

        Args:
            task_id: UUID string of ImportTask to process

        Returns:
            {"success": bool, "task_id": str, "message": str}
        """
        task_uuid = uuid.UUID(task_id)

        try:
            # Fetch task
            task = self.db.query(ImportTask).filter(ImportTask.id == task_uuid).first()
            if not task:
                logger.error(f"Task {task_id} not found in database")
                return {"success": False, "task_id": task_id, "message": "Task not found"}

            logger.info(
                f"Starting import task {task_id}: "
                f"{task.exam_code}/{task.category_code}/{task.subject_code}"
            )

            # Mark as processing
            result = self.task_service.start_processing(task_uuid)
            if result.get("error"):
                return {"success": False, "task_id": task_id, "message": result.get("message")}

            # Step 1: Validate file paths
            if not task.question_pdf_path or not task.answer_pdf_path:
                error_msg = "Missing PDF file paths"
                self.task_service.mark_failed(task_uuid, error_msg)
                return {"success": False, "task_id": task_id, "message": error_msg}

            # Step 2: Extract questions from PDFs (Phase 1)
            # 修正（2026-04-28）：extract_questions_from_pdf 簽名為
            #   (pdf_content: bytes, exam_code, category_code, subject_code, exam_name=...)
            # 並回 Tuple[ExamPaperData|None, errors:list]，先前傳 (path, path) 全錯。
            logger.info(f"Extracting questions from {task.question_pdf_path}")
            try:
                with open(task.question_pdf_path, "rb") as f:
                    pdf_bytes = f.read()
            except OSError as e:
                error_msg = f"Read PDF failed: {e}"
                self.task_service.mark_failed(task_uuid, error_msg)
                return {"success": False, "task_id": task_id, "message": error_msg}

            exam_paper, extraction_errors = self.extraction_service.extract_questions_from_pdf(
                pdf_bytes,
                exam_code=task.exam_code,
                category_code=task.category_code,
                subject_code=task.subject_code,
                exam_name=task.exam_name,
            )

            if extraction_errors:
                logger.warning(f"Extraction errors (non-fatal): {extraction_errors}")
            if not exam_paper:
                error_msg = (
                    f"No exam paper data extracted: "
                    f"{'; '.join(extraction_errors) if extraction_errors else 'unknown'}"
                )
                self.task_service.mark_failed(task_uuid, error_msg)
                return {"success": False, "task_id": task_id, "message": error_msg}

            total_questions = len(exam_paper.questions)
            logger.info(f"Extracted {total_questions} questions")

            # Update task: mark validating phase
            self.task_service.mark_validating(task_uuid, total_questions)
            self.task_service.update_progress(task_uuid, total_questions, 0, 0, 25)

            # Step 3: Run validation gates (Phase 1)
            logger.info("Running validation gates")
            validation_result = self.extraction_service.validate_exam_paper(
                exam_paper, exam_paper.answer_sheet
            )

            can_import = validation_result.can_proceed
            valid_count = len([q for q in exam_paper.questions if not validation_result.validation_details.get(str(q.question_number), {}).get("has_errors", True)])

            if not can_import:
                # Critical errors - mark for manual review
                critical_errors = validation_result.critical_errors or []
                error_summary = json.dumps({
                    "critical_errors": [str(e) for e in critical_errors],
                    "warnings": [str(w) for w in (validation_result.warnings or [])]
                })
                logger.warning(f"Validation failed for task {task_id}: {error_summary}")
                self.task_service.mark_validating(task_uuid, total_questions)
                self.task_service.mark_failed(
                    task_uuid,
                    "Validation gates failed",
                    validation_errors=error_summary
                )
                self.task_service.set_manual_review(task_uuid, "Validation critical errors")
                return {
                    "success": False,
                    "task_id": task_id,
                    "message": "Validation failed - requires manual review",
                    "error_count": total_questions - valid_count
                }

            self.task_service.update_progress(task_uuid, total_questions, valid_count, total_questions - valid_count, 40)

            # Step 4: Convert to legacy format (Phase 1)
            logger.info("Converting to legacy import format")
            legacy_result = self.extraction_service.convert_to_legacy_format(exam_paper, exam_paper.answer_sheet)
            if legacy_result.get("error"):
                error_msg = f"Conversion failed: {legacy_result.get('message')}"
                self.task_service.mark_failed(task_uuid, error_msg)
                return {"success": False, "task_id": task_id, "message": error_msg}

            legacy_output = legacy_result.get("legacy_output")

            # Step 5: Mark importing phase
            self.task_service.mark_importing(task_uuid)

            # Step 6: Import to database (Phase 2)
            # 修正（2026-04-28）：補上 import_exam_paper 必填參數 + subject_name；
            # subject_name 缺漏會讓 F26 自動觸發在 Subject lookup 階段失敗（fallback by name 找不到）。
            logger.info("Starting database import")
            import_result = self.import_service.import_exam_paper(
                legacy_output,
                exam_code=task.exam_code,
                category_code=task.category_code,
                subject_code=task.subject_code,
                exam_name=task.exam_name,
                subject_name=task.exam_name,  # 暫以 exam_name 充當 subject_name；前端表單缺獨立欄位
                tenant_id=task.tenant_id,
                skip_existing=False,
            )

            if import_result.get("error"):
                error_msg = f"Database import failed: {import_result.get('message')}"
                self.task_service.mark_failed(task_uuid, error_msg)
                return {"success": False, "task_id": task_id, "message": error_msg}

            imported_count = import_result.get("questions_imported", 0)
            exam_id = import_result.get("exam_id")
            if not exam_id:
                error_msg = "No exam_id returned from import"
                self.task_service.mark_failed(task_uuid, error_msg)
                return {"success": False, "task_id": task_id, "message": error_msg}

            exam_uuid = uuid.UUID(exam_id)

            # Step 7: Mark completed
            logger.info(f"Marking task {task_id} as completed")
            self.task_service.mark_completed(
                task_uuid,
                questions_imported=imported_count,
                historical_exam_id=exam_uuid,
                quality_gates_passed=True
            )

            logger.info(f"Import task {task_id} completed successfully: {imported_count} questions imported")
            return {
                "success": True,
                "task_id": task_id,
                "message": f"Successfully imported {imported_count} questions",
                "exam_id": exam_id,
                "questions_imported": imported_count
            }

        except Exception as e:
            logger.exception(f"Unexpected error in import task {task_id}")
            error_msg = f"Internal error: {str(e)}"
            try:
                self.task_service.mark_failed(task_uuid, error_msg)
            except Exception as inner_e:
                logger.exception(f"Failed to mark task as failed: {str(inner_e)}")

            return {
                "success": False,
                "task_id": task_id,
                "message": error_msg
            }

    def reprocess_failed_task(self, task_id: str) -> dict:
        """Attempt to reprocess a failed task.

        Args:
            task_id: UUID string of ImportTask to retry

        Returns:
            {"success": bool, "task_id": str, "retry_count": int}
        """
        task_uuid = uuid.UUID(task_id)
        task = self.db.query(ImportTask).filter(ImportTask.id == task_uuid).first()

        if not task:
            return {"success": False, "task_id": task_id, "message": "Task not found"}

        if task.retry_count >= 3:
            return {
                "success": False,
                "task_id": task_id,
                "message": "Maximum retry attempts exceeded"
            }

        # Reset task to pending
        result = self.task_service.increment_retry_count(task_uuid)
        if result.get("error"):
            return {"success": False, "task_id": task_id, "message": result.get("message")}

        # Reprocess
        return self.process_import_task(task_id)

    def get_job_statistics(self) -> dict:
        """Get import job statistics for monitoring dashboard.

        Returns:
            {"in_progress": int, "completed": int, "failed": int, "success_rate": float}
        """
        try:
            from app.models.import_task import ImportTaskStatus

            total_jobs = self.db.query(ImportTask).count()
            pending = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.PENDING).count()
            processing = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.PROCESSING).count()
            validating = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.VALIDATING).count()
            importing = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.IMPORTING).count()
            completed = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.COMPLETED).count()
            failed = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.FAILED).count()
            cancelled = self.db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.CANCELLED).count()

            in_progress = pending + processing + validating + importing
            success_rate = (completed / total_jobs * 100) if total_jobs > 0 else 0

            return {
                "total_jobs": total_jobs,
                "in_progress": in_progress,
                "pending": pending,
                "processing": processing,
                "validating": validating,
                "importing": importing,
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled,
                "success_rate": round(success_rate, 2)
            }
        except Exception as e:
            logger.exception(f"Failed to get statistics: {str(e)}")
            return {}
