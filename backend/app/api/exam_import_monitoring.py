"""Monitoring Dashboard endpoints for import job tracking (Phase 3)."""

import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user_id
from app.services.import_background_worker import ImportBackgroundWorker
from app.services.import_audit_log_service import ImportAuditLogService
from app.services.import_task_service import ImportTaskService
from app.models import ImportTask
from app.models.import_task import ImportTaskStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exam-import", tags=["exam-import-monitoring"])


@router.get("/dashboard/stats")
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
) -> dict:
    """Get comprehensive import statistics for dashboard.

    Returns:
        Job stats, success rates, trends
    """
    try:
        worker = ImportBackgroundWorker(db)
        audit_service = ImportAuditLogService(db)

        # Get job statistics
        job_stats = worker.get_job_statistics()
        audit_stats = audit_service.get_import_statistics()

        if not job_stats or audit_stats.get("error"):
            raise HTTPException(
                status_code=500,
                detail={"message": "Failed to compute statistics"}
            )

        audit_data = audit_stats  # ok() flattened

        # Calculate average duration
        avg_duration_ms = audit_data.get("average_duration_ms", 0)
        avg_duration_sec = int(avg_duration_ms / 1000) if avg_duration_ms else 0

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "job_queue": {
                "total_jobs": job_stats.get("total_jobs", 0),
                "in_progress": job_stats.get("in_progress", 0),
                "pending": job_stats.get("pending", 0),
                "processing": job_stats.get("processing", 0),
                "validating": job_stats.get("validating", 0),
                "importing": job_stats.get("importing", 0),
                "completed": job_stats.get("completed", 0),
                "failed": job_stats.get("failed", 0),
                "cancelled": job_stats.get("cancelled", 0),
            },
            "success_metrics": {
                "success_rate": job_stats.get("success_rate", 0),
                "successful_jobs": audit_data.get("successful", 0),
                "failed_jobs": audit_data.get("failed", 0),
                "average_duration_seconds": avg_duration_sec,
            },
            "import_volume": {
                "total_questions_imported": audit_data.get("total_questions_imported", 0),
                "average_questions_per_job": (
                    audit_data.get("total_questions_imported", 0) // audit_data.get("successful", 1)
                    if audit_data.get("successful", 0) > 0 else 0
                ),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/dashboard/recent-jobs")
async def get_recent_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    """Get recently updated import jobs.

    Args:
        limit: Number of jobs to return (default 20)

    Returns:
        List of recent jobs with status
    """
    try:
        # ImportTask has no `updated_at` column; sort by completed_at when
        # present, falling back to created_at.
        from sqlalchemy import desc, func as sa_func
        jobs = db.query(ImportTask).order_by(
            desc(sa_func.coalesce(ImportTask.completed_at, ImportTask.created_at))
        ).limit(limit).all()

        recent_jobs = [
            {
                "task_id": str(job.id),
                "exam": f"{job.exam_code}/{job.category_code}/{job.subject_code}",
                "status": job.status,
                "progress_percent": job.progress_percent,
                "questions_imported": job.questions_imported,
                "total_questions": job.total_questions,
                "created_at": job.created_at,
                "completed_at": job.completed_at,
                "error": job.error_message,
            }
            for job in jobs
        ]

        return {
            "recent_jobs": recent_jobs,
            "count": len(recent_jobs),
        }

    except Exception as e:
        logger.exception(f"Failed to get recent jobs: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/dashboard/status-breakdown")
async def get_status_breakdown(
    db: Session = Depends(get_db),
) -> dict:
    """Get breakdown of jobs by status.

    Returns:
        Counts for each status with percentage
    """
    try:
        task_service = ImportTaskService(db)

        total = db.query(ImportTask).count()

        statuses = {
            "pending": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.PENDING).count(),
            "processing": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.PROCESSING).count(),
            "validating": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.VALIDATING).count(),
            "importing": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.IMPORTING).count(),
            "completed": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.COMPLETED).count(),
            "failed": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.FAILED).count(),
            "cancelled": db.query(ImportTask).filter(ImportTask.status == ImportTaskStatus.CANCELLED).count(),
        }

        breakdown = {
            status: {
                "count": count,
                "percentage": round((count / total * 100) if total > 0 else 0, 2)
            }
            for status, count in statuses.items()
        }

        return {
            "total_jobs": total,
            "breakdown": breakdown,
        }

    except Exception as e:
        logger.exception(f"Failed to get status breakdown: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/dashboard/performance-metrics")
async def get_performance_metrics(
    days: int = 7,
    db: Session = Depends(get_db),
) -> dict:
    """Get performance metrics over time period.

    Args:
        days: Number of days to analyze (default 7)

    Returns:
        Performance trends and metrics
    """
    try:
        audit_service = ImportAuditLogService(db)

        # Get jobs from last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        jobs_in_period = db.query(ImportTask).filter(
            ImportTask.created_at >= cutoff_date
        ).all()

        if not jobs_in_period:
            return {
                "period_days": days,
                "message": "No import jobs in this period",
                "metrics": {
                    "total_jobs": 0,
                    "successful": 0,
                    "failed": 0,
                    "average_duration_seconds": 0,
                }
            }

        # Calculate metrics
        successful = sum(1 for j in jobs_in_period if j.status == ImportTaskStatus.COMPLETED)
        failed = sum(1 for j in jobs_in_period if j.status == ImportTaskStatus.FAILED)
        total_questions = sum(j.questions_imported or 0 for j in jobs_in_period if j.status == ImportTaskStatus.COMPLETED)

        # Calculate average duration
        completed_jobs = [j for j in jobs_in_period if j.status == ImportTaskStatus.COMPLETED and j.completed_at]
        avg_duration_sec = 0
        if completed_jobs:
            total_duration = sum((j.completed_at - j.started_at).total_seconds() for j in completed_jobs if j.started_at)
            avg_duration_sec = int(total_duration / len(completed_jobs))

        return {
            "period_days": days,
            "period_end": datetime.utcnow().isoformat(),
            "metrics": {
                "total_jobs": len(jobs_in_period),
                "successful": successful,
                "failed": failed,
                "success_rate": round((successful / len(jobs_in_period) * 100) if jobs_in_period else 0, 2),
                "average_duration_seconds": avg_duration_sec,
                "total_questions_imported": total_questions,
            }
        }

    except Exception as e:
        logger.exception(f"Failed to get performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/dashboard/job-details/{task_id}")
async def get_job_details(
    task_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Get detailed information about a specific job.

    Args:
        task_id: Task UUID

    Returns:
        Complete job details and audit trail
    """
    try:
        import uuid
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"message": "Invalid task_id format"})

    try:
        task_service = ImportTaskService(db)
        audit_service = ImportAuditLogService(db)

        # Get task details
        task_result = task_service.get_task_status(task_uuid)
        if task_result.get("error"):
            raise HTTPException(status_code=404, detail={"message": "Task not found"})

        task_data = task_result  # ok() flattened

        # Get audit trail
        audit_result = audit_service.get_task_audit_trail(task_uuid)
        audit_trail = audit_result.get("audit_trail", []) if not audit_result.get("error") else []

        # Calculate timeline
        start_time = task_data.get("started_at")
        end_time = task_data.get("completed_at")
        duration_sec = None
        if start_time and end_time:
            from datetime import datetime as _dt
            def _to_dt(v):
                if isinstance(v, _dt):
                    return v
                if isinstance(v, str):
                    return _dt.fromisoformat(v.replace('Z', '+00:00'))
                return None
            start = _to_dt(start_time)
            end = _to_dt(end_time)
            if start and end:
                duration_sec = int((end - start).total_seconds())

        return {
            "task": {
                "task_id": task_data["task_id"],
                "exam": f"{task_data['exam_code']}/{task_data['category_code']}/{task_data['subject_code']}",
                "status": task_data["status"],
                "progress_percent": task_data["progress_percent"],
            },
            "statistics": {
                "total_questions": task_data["total_questions"],
                "processed": task_data["questions_processed"],
                "valid": task_data["questions_valid"],
                "invalid": task_data["questions_invalid"],
                "imported": task_data["questions_imported"],
            },
            "timeline": {
                "created_at": task_data["created_at"],
                "started_at": task_data.get("started_at"),
                "completed_at": task_data.get("completed_at"),
                "duration_seconds": duration_sec,
            },
            "quality": {
                "quality_gates_passed": task_data["quality_gates_passed"],
                "requires_manual_review": task_data["requires_manual_review"],
                "retry_count": task_data.get("retry_count", 0),
            },
            "error": {
                "error_message": task_data.get("error_message"),
                "validation_errors": task_data.get("validation_errors"),
                "import_errors": task_data.get("import_errors"),
            },
            "audit_trail": audit_trail,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get job details: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})


@router.get("/dashboard/failed-jobs")
async def get_failed_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    """Get list of failed import jobs for review.

    Args:
        limit: Number of jobs to return

    Returns:
        Failed jobs with error details
    """
    try:
        failed_jobs = db.query(ImportTask).filter(
            ImportTask.status == ImportTaskStatus.FAILED
        ).order_by(
            ImportTask.completed_at.desc()
        ).limit(limit).all()

        jobs_list = [
            {
                "task_id": str(job.id),
                "exam": f"{job.exam_code}/{job.category_code}/{job.subject_code}",
                "error_message": job.error_message,
                "retry_count": job.retry_count,
                "failed_at": job.completed_at,
                "can_retry": job.retry_count < 3,
            }
            for job in failed_jobs
        ]

        return {
            "failed_jobs": jobs_list,
            "count": len(jobs_list),
        }

    except Exception as e:
        logger.exception(f"Failed to get failed jobs: {str(e)}")
        raise HTTPException(status_code=500, detail={"message": str(e)})
