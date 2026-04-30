"""Feedback API — 意見反饋。"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user_id
from app.models.user import User
from app.services.feedback_service import FeedbackService

router = APIRouter(prefix="/feedback")


class AttachmentMeta(BaseModel):
    """附件元數據（測試 / API 用）。"""
    file_path: str
    file_size: int
    mime_type: str = "image/png"


class SubmitFeedbackRequest(BaseModel):
    type: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    attachments: Optional[list[AttachmentMeta]] = None


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
    """管理員查看所有反饋清單，可依狀態篩選。"""
    _check_admin(user_id, db)
    service = FeedbackService(db)
    return service.admin_list_feedbacks(status_filter=status)


@router.get("/admin/stats")
def admin_get_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """管理員查看反饋統計摘要。"""
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
    """管理員更新反饋狀態並可回覆使用者。"""
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
    body: SubmitFeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """提交意見反饋（JSON body）。附件以元數據方式傳入。"""
    service = FeedbackService(db)

    attachment_data = None
    if body.attachments:
        attachment_data = [
            {
                "file_path": att.file_path,
                "file_size": att.file_size,
                "mime_type": att.mime_type,
            }
            for att in body.attachments
        ]

    result = service.submit_feedback(
        user_id=user_id,
        feedback_type=body.type or "",
        subject=body.subject or "",
        content=body.content or "",
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
    """使用者查看自己的反饋清單。"""
    service = FeedbackService(db)
    return service.list_user_feedbacks(user_id)


@router.get("/{feedback_id}")
def get_feedback_detail(
    feedback_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """使用者查看單筆反饋詳情。"""
    service = FeedbackService(db)
    result = service.get_feedback_detail(user_id, feedback_id)
    if result.get("error"):
        raise HTTPException(
            status_code=result.get("status_code", 400),
            detail={"message": result["message"]},
        )
    return result
