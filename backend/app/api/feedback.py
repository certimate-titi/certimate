"""Feedback API — 意見反饋。"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.models.user import User
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback")


class SubmitFeedbackRequest(BaseModel):
    type: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[list[dict]] = None


class UpdateFeedbackRequest(BaseModel):
    status: str
    admin_reply: Optional[str] = None
    close_reason: Optional[str] = None


def _check_admin(user_id: str, db: Session):
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    user_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
    if user_role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail={"message": "權限不足"})


# === Admin routes MUST come before /{feedback_id} to avoid path conflicts ===

@router.get("/admin/list")
def admin_list_feedbacks(
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _check_admin(user_id, db)
    service = FeedbackService(db)
    return service.admin_list_feedbacks(status_filter=status)


@router.get("/admin/stats")
def admin_get_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _check_admin(user_id, db)
    service = FeedbackService(db)
    return service.admin_get_stats()


@router.put("/admin/{feedback_id}")
def admin_update_feedback(
    feedback_id: str,
    body: UpdateFeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    _check_admin(user_id, db)
    service = FeedbackService(db)
    result = service.admin_update_feedback(
        admin_id=user_id,
        feedback_id=feedback_id,
        new_status=body.status,
        admin_reply=body.admin_reply,
        close_reason=body.close_reason,
    )
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


# === User routes ===

@router.post("")
def submit_feedback(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    # Accept both JSON body and multipart/form-data (frontend sends FormData for file uploads)
    type: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    attachments: Optional[list[UploadFile]] = File(None),
):
    from app.models.feedback import FeedbackAttachment
    service = FeedbackService(db)

    # Convert uploaded files to attachment metadata
    attachment_data = None
    if attachments:
        attachment_data = []
        for f in attachments:
            if f.filename:
                file_bytes = f.file.read()
                # Store as base64 in DB for simplicity (small files ≤ 5MB)
                import base64
                attachment_data.append({
                    "filename": f.filename,
                    "content_type": f.content_type or "image/png",
                    "size": len(file_bytes),
                    "data_b64": base64.b64encode(file_bytes).decode("utf-8")[:500000],  # cap at ~375KB
                })

    result = service.submit_feedback(
        user_id=user_id,
        feedback_type=type or "",
        subject=subject or "",
        content=content or "",
        attachments=attachment_data,
    )
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result


@router.get("")
def list_my_feedbacks(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = FeedbackService(db)
    return service.list_user_feedbacks(user_id)


@router.get("/{feedback_id}")
def get_feedback_detail(
    feedback_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service = FeedbackService(db)
    result = service.get_feedback_detail(user_id, feedback_id)
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result
