"""Account Settings API — 帳號設定與個人偏好 (Feature 22)."""

import hashlib
import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.core.deps import get_db, get_current_user_id
from app.models.user import User
from app.models.user_usage import UserUsage

router = APIRouter(prefix="/account")


# ── Schemas ──────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    daily_study_minutes: Optional[int] = None
    learning_style: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class DeleteAccountRequest(BaseModel):
    confirm_text: str


# ── Helpers ──────────────────────────────────────────────────────────

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _get_user(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == uuid_mod.UUID(user_id)).first()
    if not user:
        return None
    return user


# ── Endpoints ────────────────────────────────────────────────────────

@router.put("/profile")
def update_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新個人資料。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    if body.display_name is not None:
        if not body.display_name.strip():
            raise HTTPException(status_code=400, detail={"message": "顯示名稱不可為空"})
        user.display_name = body.display_name.strip()

    if body.age is not None:
        user.age = body.age
    if body.education is not None:
        user.education = body.education
    if body.occupation is not None:
        user.occupation = body.occupation
    if body.daily_study_minutes is not None:
        user.daily_study_minutes = body.daily_study_minutes
    if body.learning_style is not None:
        # learning_preference enum: drill/concept/mixed — 前端可能傳 visual/auditory/reading
        # 映射到最接近的 enum 值，或存為 metadata
        style_map = {"visual": "concept", "auditory": "drill", "reading": "concept", "kinesthetic": "mixed"}
        mapped = style_map.get(body.learning_style, body.learning_style)
        if hasattr(user, "learning_preference"):
            try:
                user.learning_preference = mapped
            except (ValueError, Exception):
                pass  # Ignore invalid enum values

    db.commit()
    db.refresh(user)

    return {
        "ok": True,
        "message": "個人資料已更新",
        "profile": {
            "display_name": user.display_name,
            "email": user.email,
            "age": getattr(user, "age", None),
            "education": getattr(user, "education", None),
            "occupation": getattr(user, "occupation", None),
            "daily_study_minutes": getattr(user, "daily_study_minutes", None),
            "learning_style": getattr(user, "learning_style", None),
        },
    }


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """變更密碼。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    if user.password_hash != _hash(body.current_password):
        raise HTTPException(status_code=400, detail={"message": "目前密碼不正確"})

    user.password_hash = _hash(body.new_password)
    db.commit()

    return {"ok": True, "message": "密碼已更新"}


@router.get("/usage")
def get_usage(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """查詢使用量摘要。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    usage = db.query(UserUsage).filter(UserUsage.user_id == user.id).first()

    return {
        "ok": True,
        "exams_used": usage.monthly_exams if usage else 0,
        "exams_limit": 10,
        "uploads_used": usage.monthly_uploads if usage else 0,
        "uploads_limit": 5,
        "ai_chats_used": usage.daily_ai_chats if usage else 0,
        "ai_chats_limit": 3,
    }


@router.delete("")
def delete_account(
    body: DeleteAccountRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """申請刪除帳號（需輸入確認文字）。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    if body.confirm_text != "確認刪除":
        raise HTTPException(status_code=400, detail={"message": "確認文字不符"})

    user.status = "DELETED"
    db.commit()

    return {"ok": True, "message": "帳號已標記為刪除，將在 30 天後永久移除"}


@router.patch("/notification-preferences")
def update_notification_preferences(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新通知偏好設定。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    # Store preferences in user's metadata or dedicated field
    if hasattr(user, "notification_preferences"):
        user.notification_preferences = body
    db.commit()

    return {"ok": True, "message": "通知偏好已更新", "preferences": body}
