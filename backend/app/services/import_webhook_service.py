"""ImportWebhookService — Post-import event notifications (Phase 3)."""

import json
import logging
import uuid
import httpx
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.base import BaseService

logger = logging.getLogger(__name__)

# Webhook timeout (seconds)
WEBHOOK_TIMEOUT = 10

# Supported webhook events
WEBHOOK_EVENTS = {
    "import.task.created",
    "import.extraction.complete",
    "import.validation.complete",
    "import.completed",
    "import.failed",
    "import.rolled_back",
}


class ImportWebhookService(BaseService):
    """Send event notifications to configured webhooks."""

    def __init__(self, db: Session = None):
        """Initialize service with optional database session."""
        super().__init__(db)

    async def send_webhook(
        self,
        webhook_url: str,
        event: str,
        payload: dict,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> dict:
        """Send webhook notification to configured URL.

        Args:
            webhook_url: Webhook endpoint URL
            event: Event type (e.g., 'import.completed')
            payload: Event payload dict
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts

        Returns:
            {"success": bool, "status_code": int, "message": str}
        """
        if event not in WEBHOOK_EVENTS:
            return self.error(400, f"Unknown event type: {event}")

        try:
            # Build webhook payload
            webhook_payload = {
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload,
            }

            # Send POST request
            async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
                response = await client.post(
                    webhook_url,
                    json=webhook_payload,
                    headers={"Content-Type": "application/json"},
                )

                success = response.status_code in (200, 201, 202, 204)

                if success:
                    logger.info(
                        f"Webhook sent successfully: {event} to {webhook_url} "
                        f"(status={response.status_code})"
                    )
                    return self.ok({
                        "success": True,
                        "status_code": response.status_code,
                        "message": "Webhook sent successfully",
                    })

                # Retry on server errors or timeout
                if response.status_code >= 500 and retry_count < max_retries:
                    logger.warning(
                        f"Webhook error (will retry): {event} to {webhook_url} "
                        f"(attempt {retry_count + 1}/{max_retries}, status={response.status_code})"
                    )
                    # Recursive retry
                    return await self.send_webhook(
                        webhook_url,
                        event,
                        payload,
                        retry_count=retry_count + 1,
                        max_retries=max_retries,
                    )

                # Non-retryable error
                logger.error(
                    f"Webhook failed: {event} to {webhook_url} "
                    f"(status={response.status_code})"
                )
                return self.error(
                    response.status_code,
                    f"Webhook request failed: {response.text[:200]}"
                )

        except httpx.TimeoutException:
            if retry_count < max_retries:
                logger.warning(
                    f"Webhook timeout (will retry): {event} to {webhook_url} "
                    f"(attempt {retry_count + 1}/{max_retries})"
                )
                return await self.send_webhook(
                    webhook_url,
                    event,
                    payload,
                    retry_count=retry_count + 1,
                    max_retries=max_retries,
                )

            logger.error(f"Webhook timeout (max retries): {event} to {webhook_url}")
            return self.error(504, "Webhook request timed out")

        except Exception as e:
            logger.exception(f"Webhook error: {event} to {webhook_url}: {str(e)}")
            return self.error(500, f"Webhook failed: {str(e)}")

    async def notify_task_created(
        self,
        webhook_url: str,
        task_id: str,
        exam_code: str,
        category_code: str,
        subject_code: str,
        exam_name: Optional[str] = None,
    ) -> dict:
        """Notify webhook about new import task.

        Args:
            webhook_url: Webhook endpoint
            task_id: Task UUID
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            exam_name: Optional exam name

        Returns:
            Webhook send result
        """
        payload = {
            "task_id": task_id,
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
            "exam_name": exam_name,
        }

        return await self.send_webhook(webhook_url, "import.task.created", payload)

    async def notify_extraction_complete(
        self,
        webhook_url: str,
        task_id: str,
        exam_code: str,
        category_code: str,
        subject_code: str,
        questions_extracted: int,
        questions_valid: int,
        questions_invalid: int,
    ) -> dict:
        """Notify webhook about extraction completion.

        Args:
            webhook_url: Webhook endpoint
            task_id: Task UUID
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            questions_extracted: Total questions found
            questions_valid: Valid questions
            questions_invalid: Invalid questions

        Returns:
            Webhook send result
        """
        payload = {
            "task_id": task_id,
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
            "extraction_stats": {
                "total": questions_extracted,
                "valid": questions_valid,
                "invalid": questions_invalid,
            },
        }

        return await self.send_webhook(webhook_url, "import.extraction.complete", payload)

    async def notify_validation_complete(
        self,
        webhook_url: str,
        task_id: str,
        exam_code: str,
        category_code: str,
        subject_code: str,
        can_proceed: bool,
        critical_errors: Optional[list] = None,
        warnings: Optional[list] = None,
    ) -> dict:
        """Notify webhook about validation completion.

        Args:
            webhook_url: Webhook endpoint
            task_id: Task UUID
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            can_proceed: Whether validation passed
            critical_errors: List of critical errors
            warnings: List of warnings

        Returns:
            Webhook send result
        """
        payload = {
            "task_id": task_id,
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
            "can_proceed": can_proceed,
            "critical_errors": critical_errors or [],
            "warnings": warnings or [],
        }

        return await self.send_webhook(webhook_url, "import.validation.complete", payload)

    async def notify_import_completed(
        self,
        webhook_url: str,
        task_id: str,
        exam_code: str,
        category_code: str,
        subject_code: str,
        historical_exam_id: str,
        questions_imported: int,
        duration_ms: int,
    ) -> dict:
        """Notify webhook about successful import completion.

        Args:
            webhook_url: Webhook endpoint
            task_id: Task UUID
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            historical_exam_id: Created exam ID
            questions_imported: Number of questions imported
            duration_ms: Import duration in milliseconds

        Returns:
            Webhook send result
        """
        payload = {
            "task_id": task_id,
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
            "historical_exam_id": historical_exam_id,
            "questions_imported": questions_imported,
            "duration_ms": duration_ms,
        }

        return await self.send_webhook(webhook_url, "import.completed", payload)

    async def notify_import_failed(
        self,
        webhook_url: str,
        task_id: str,
        exam_code: str,
        category_code: str,
        subject_code: str,
        error_message: str,
        retry_count: int = 0,
    ) -> dict:
        """Notify webhook about import failure.

        Args:
            webhook_url: Webhook endpoint
            task_id: Task UUID
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            error_message: Failure reason
            retry_count: Current retry attempt

        Returns:
            Webhook send result
        """
        payload = {
            "task_id": task_id,
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
            "error_message": error_message,
            "retry_count": retry_count,
            "max_retries": 3,
        }

        return await self.send_webhook(webhook_url, "import.failed", payload)

    async def notify_import_rolled_back(
        self,
        webhook_url: str,
        task_id: str,
        exam_code: str,
        category_code: str,
        subject_code: str,
        questions_deleted: int,
        reason: Optional[str] = None,
    ) -> dict:
        """Notify webhook about rollback operation.

        Args:
            webhook_url: Webhook endpoint
            task_id: Task UUID
            exam_code: Exam code
            category_code: Category code
            subject_code: Subject code
            questions_deleted: Number of questions removed
            reason: Optional reason for rollback

        Returns:
            Webhook send result
        """
        payload = {
            "task_id": task_id,
            "exam_code": exam_code,
            "category_code": category_code,
            "subject_code": subject_code,
            "questions_deleted": questions_deleted,
            "reason": reason,
        }

        return await self.send_webhook(webhook_url, "import.rolled_back", payload)


# Factory function for getting webhook service (async support)
def get_import_webhook_service(db: Session = None) -> ImportWebhookService:
    """Get webhook service instance."""
    return ImportWebhookService(db)
