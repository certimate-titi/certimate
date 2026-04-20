"""Async exam import endpoints (Phase 3 — Background job processing)."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_id, get_db_with_tenant, get_tenant_id
from app.services.import_task_service import ImportTaskService
from app.services.import_scheduler import schedule_import_job, cancel_import_job, get_scheduler
from app.services.import_background_worker import ImportBackgroundWorker
import tempfile
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exam-import", tags=["exam-import"])


@router.post("/async")
async def submit_async_import(
    question_pdf: UploadFile = File(...),
    answer_pdf: UploadFile = File(...),
    exam_code: str = Form(...),
    category_code: str = Form(...),
    subject_code: str = Form(...),
    exam_name: Optional[str] = Form(None),
    user_id: uuid.UUID = Depends(get_current_user_id),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db_with_tenant),
) -> dict:
    """Submit an exam import job to background queue.

    Returns immediately with task_id. Actual import happens asynchronously.

    Args:
        question_pdf: Question PDF file
        answer_pdf: Answer PDF file
        exam_code: Exam code (e.g., 'P')
        category_code: Category code (e.g., '01')
        subject_code: Subject code (e.g., '0101')
        exam_name: Optional exam name
        user_id: Current user ID (from JWT)
        db: Database session with tenant isolation

    Returns:
        {"task_id": str, "status": "pending", "message": "Job queued"}

    Raises:
        HTTPException: 400 if scheduler not initialized
    """
    try:
        # Validate scheduler is running
        scheduler = get_scheduler()
        if scheduler is None:
            raise HTTPException(
                status_code=500,
                detail={"message": "Import service not ready - scheduler not initialized"}
            )

        # Save PDFs to temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as q_file:
            q_file.write(await question_pdf.read())
            question_pdf_path = q_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as a_file:
            a_file.write(await answer_pdf.read())
            answer_pdf_path = a_file.name

        # Get file sizes
        import os
        q_file_size = os.path.getsize(question_pdf_path)
        a_file_size = os.path.getsize(answer_pdf_path)
        total_size = q_file_size + a_file_size

        # Create import task
        task_service = ImportTaskService(db)
        result = task_service.create_import_task(
            user_id=user_id,
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            exam_name=exam_name,
            question_pdf_path=question_pdf_path,
            answer_pdf_path=answer_pdf_path,
            pdf_file_size=total_size,
            tenant_id=tenant_id,
        )

        if result.get("error"):
            raise HTTPException(
                status_code=400,
                detail={"message": result.get("message")}
            )

        task_id = result.get("data", {}).get("task_id")

        # Schedule background job
        job_id = schedule_import_job(task_id, immediate=True)
        if not job_id:
            raise HTTPException(
                status_code=500,
                detail={"message": "Failed to schedule import job"}
            )

        logger.info(f"Queued import job: task_id={task_id}, job_id={job_id}, exam={exam_code}/{category_code}/{subject_code}")

        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Import job queued - processing will begin shortly",
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to submit import job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"message": f"Internal error: {str(e)}"}
        )


@router.get("/tasks/{task_id}")
async def get_import_task_status(
    task_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Get status of an import task.

    Args:
        task_id: Task UUID
        user_id: Current user ID
        db: Database session

    Returns:
        Task status, progress, error details

    Raises:
        HTTPException: 404 if task not found or not authorized
    """
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"message": "Invalid task_id format"})

    try:
        task_service = ImportTaskService(db)
        result = task_service.get_task_status(task_uuid)

        if result.get("error"):
            raise HTTPException(status_code=404, detail={"message": "Task not found"})

        task_data = result.get("data", {})

        # Verify user owns this task
        if str(user_id) != task_data.get("user_id"):
            raise HTTPException(status_code=403, detail={"message": "Not authorized to view this task"})

        return {
            "task_id": task_data["task_id"],
            "status": task_data["status"],
            "exam_code": task_data["exam_code"],
            "category_code": task_data["category_code"],
            "subject_code": task_data["subject_code"],
            "progress_percent": task_data["progress_percent"],
            "total_questions": task_data["total_questions"],
            "questions_processed": task_data["questions_processed"],
            "questions_valid": task_data["questions_valid"],
            "questions_invalid": task_data["questions_invalid"],
            "questions_imported": task_data["questions_imported"],
            "quality_gates_passed": task_data["quality_gates_passed"],
            "requires_manual_review": task_data["requires_manual_review"],
            "error_message": task_data.get("error_message"),
            "created_at": task_data["created_at"],
            "started_at": task_data.get("started_at"),
            "completed_at": task_data.get("completed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get task status: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.post("/tasks/{task_id}/cancel")
async def cancel_import_task(
    task_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel a pending or processing import task.

    Args:
        task_id: Task UUID to cancel
        user_id: Current user ID
        db: Database session

    Returns:
        {"status": "cancelled", "message": "Task cancelled"}

    Raises:
        HTTPException: 404 if task not found, 400 if cannot cancel
    """
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"message": "Invalid task_id format"})

    try:
        task_service = ImportTaskService(db)

        # Get task to verify ownership
        status_result = task_service.get_task_status(task_uuid)
        if status_result.get("error"):
            raise HTTPException(status_code=404, detail={"message": "Task not found"})

        task_data = status_result.get("data", {})
        if str(user_id) != task_data.get("user_id"):
            raise HTTPException(status_code=403, detail={"message": "Not authorized"})

        # Cancel in scheduler
        cancelled = cancel_import_job(task_id)

        # Mark as cancelled in database
        result = task_service.mark_cancelled(task_uuid)
        if result.get("error"):
            raise HTTPException(status_code=400, detail={"message": result.get("message")})

        logger.info(f"Cancelled import task {task_id}")

        return {
            "status": "cancelled",
            "message": "Task cancelled successfully",
            "task_id": task_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to cancel task: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/tasks")
async def list_user_import_tasks(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """List all import tasks for current user.

    Args:
        limit: Page size (default 20)
        offset: Page offset (default 0)
        status: Optional status filter (pending, processing, completed, failed, cancelled)
        user_id: Current user ID
        db: Database session

    Returns:
        Paginated task list with total count

    Raises:
        HTTPException: 400 if invalid status filter
    """
    if status and status not in ["pending", "processing", "validating", "importing", "completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail={"message": f"Invalid status: {status}"}
        )

    try:
        task_service = ImportTaskService(db)
        result = task_service.list_user_tasks(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status_filter=status,
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail={"message": result.get("message")})

        data = result.get("data", {})
        return {
            "tasks": data["tasks"],
            "total": data["total"],
            "limit": data["limit"],
            "offset": data["offset"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to list tasks: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/stats")
async def get_import_statistics(
    db: Session = Depends(get_db),
) -> dict:
    """Get import job statistics for monitoring dashboard.

    Returns:
        Job stats: in_progress, completed, failed, success_rate

    Raises:
        HTTPException: 500 if stats cannot be computed
    """
    try:
        worker = ImportBackgroundWorker(db)
        stats = worker.get_job_statistics()

        if not stats:
            raise HTTPException(status_code=500, detail={"message": "Failed to compute statistics"})

        return {
            "total_jobs": stats["total_jobs"],
            "in_progress": stats["in_progress"],
            "pending": stats["pending"],
            "processing": stats["processing"],
            "validating": stats["validating"],
            "importing": stats["importing"],
            "completed": stats["completed"],
            "failed": stats["failed"],
            "cancelled": stats["cancelled"],
            "success_rate": stats["success_rate"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})
