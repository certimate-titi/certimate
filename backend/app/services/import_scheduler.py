"""APScheduler configuration for async import job processing (Phase 3)."""

import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global scheduler instance
_scheduler: Optional[BackgroundScheduler] = None


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


def init_scheduler(database_url: str) -> BackgroundScheduler:
    """Initialize APScheduler for background import jobs.

    Uses database as job store (SQLAlchemy).
    Runs background executor with 5 worker threads.

    Args:
        database_url: SQLAlchemy database URL

    Returns:
        Initialized BackgroundScheduler instance

    Raises:
        RuntimeError if scheduler already initialized
    """
    global _scheduler

    if _scheduler is not None:
        raise RuntimeError("Scheduler already initialized")

    try:
        # Create engine for job store
        engine = create_engine(database_url)

        # Configure job store (persists jobs in database)
        jobstores = {
            "default": SQLAlchemyJobStore(engine=engine, tablename="apscheduler_jobs")
        }

        # Configure executors (thread pool for background processing)
        executors = {
            "default": ThreadPoolExecutor(max_workers=5),
        }

        # Configure job defaults
        job_defaults = {
            "coalesce": False,
            "max_instances": 1,
            "misfire_grace_time": 600,  # 10 minutes grace time
        }

        # Initialize scheduler
        _scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )

        _scheduler.start()
        logger.info("APScheduler initialized with database job store")
        return _scheduler

    except Exception as e:
        logger.exception(f"Failed to initialize scheduler: {str(e)}")
        raise


def shutdown_scheduler() -> None:
    """Shutdown the scheduler gracefully.

    Cancels all pending jobs and closes the scheduler.
    """
    global _scheduler

    if _scheduler is None:
        return

    try:
        _scheduler.shutdown(wait=True)
        logger.info("Scheduler shutdown complete")
        _scheduler = None
    except Exception as e:
        logger.exception(f"Error shutting down scheduler: {str(e)}")


def schedule_import_job(task_id: str, immediate: bool = True) -> Optional[str]:
    """Schedule an import task for processing.

    Args:
        task_id: UUID of ImportTask to process
        immediate: If True, schedule for immediate execution; if False, execute next check cycle

    Returns:
        Job ID string, or None if scheduling failed

    Raises:
        RuntimeError if scheduler not initialized
    """
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized - call init_scheduler() first")

    try:
        from app.services.import_background_worker import ImportBackgroundWorker

        # Create job
        job = _scheduler.add_job(
            _process_import_job_wrapper,
            args=(task_id,),
            id=f"import_{task_id}",
            replace_existing=True,  # Replace if job already queued
            max_instances=1,
        )

        logger.info(f"Scheduled import job for task {task_id}, job_id={job.id}")
        return job.id

    except Exception as e:
        logger.exception(f"Failed to schedule import job: {str(e)}")
        return None


def cancel_import_job(task_id: str) -> bool:
    """Cancel a scheduled import job.

    Args:
        task_id: UUID of ImportTask

    Returns:
        True if job was cancelled, False if not found or error

    Raises:
        RuntimeError if scheduler not initialized
    """
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized")

    try:
        job_id = f"import_{task_id}"
        job = _scheduler.get_job(job_id)

        if job:
            job.remove()
            logger.info(f"Cancelled import job {job_id}")
            return True

        logger.warning(f"Import job {job_id} not found")
        return False

    except Exception as e:
        logger.exception(f"Failed to cancel import job: {str(e)}")
        return False


def get_scheduled_jobs() -> dict:
    """Get list of all scheduled import jobs.

    Returns:
        {"jobs": [{"job_id": str, "task_id": str, "next_run_time": datetime}]}

    Raises:
        RuntimeError if scheduler not initialized
    """
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized")

    try:
        jobs = _scheduler.get_jobs()
        import_jobs = [
            {
                "job_id": job.id,
                "task_id": job.id.replace("import_", ""),
                "next_run_time": job.next_run_time,
                "func": str(job.func),
            }
            for job in jobs
            if job.id.startswith("import_")
        ]

        return {"jobs": import_jobs, "count": len(import_jobs)}

    except Exception as e:
        logger.exception(f"Failed to get scheduled jobs: {str(e)}")
        return {"jobs": [], "count": 0}


def _process_import_job_wrapper(task_id: str) -> dict:
    """Wrapper for APScheduler job execution.

    Creates a fresh database session and processes the import task.

    Args:
        task_id: UUID of ImportTask

    Returns:
        Job result dictionary
    """
    from app.core.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.services.import_background_worker import ImportBackgroundWorker

    try:
        # Create a fresh database session for this job
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            worker = ImportBackgroundWorker(db)
            result = worker.process_import_task(task_id)
            logger.info(f"Import job {task_id} result: {result}")
            return result
        finally:
            db.close()

    except Exception as e:
        logger.exception(f"Failed to execute import job {task_id}: {str(e)}")
        return {
            "success": False,
            "task_id": task_id,
            "message": f"Job execution failed: {str(e)}"
        }


# Periodic cleanup job (removes old completed/failed tasks)
def _cleanup_old_tasks():
    """Cleanup old import tasks (older than 30 days)."""
    from datetime import datetime, timedelta
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import ImportTask

    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        cutoff_date = datetime.utcnow() - timedelta(days=30)
        deleted = db.query(ImportTask).filter(ImportTask.created_at < cutoff_date).delete()
        db.commit()

        logger.info(f"Cleaned up {deleted} old import tasks")

    except Exception as e:
        logger.exception(f"Cleanup job failed: {str(e)}")
    finally:
        db.close()


def schedule_cleanup_job(interval_hours: int = 24) -> Optional[str]:
    """Schedule periodic cleanup of old import tasks.

    Args:
        interval_hours: How often to run cleanup (default: 24 hours)

    Returns:
        Job ID, or None if scheduling failed

    Raises:
        RuntimeError if scheduler not initialized
    """
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized")

    try:
        job = _scheduler.add_job(
            _cleanup_old_tasks,
            trigger=IntervalTrigger(hours=interval_hours),
            id="import_cleanup",
            replace_existing=True,
        )

        logger.info(f"Scheduled cleanup job every {interval_hours} hours")
        return job.id

    except Exception as e:
        logger.exception(f"Failed to schedule cleanup job: {str(e)}")
        return None
