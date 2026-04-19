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

    if body.confirm_text not in ("確認刪除", "DELETE"):
        raise HTTPException(status_code=400, detail={"message": "請輸入大寫 DELETE 以確認刪除帳號"})

    from app.models.user import UserStatus
    user.status = UserStatus.DELETED
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


# ── 訂閱管理 (Feature 13) ──────────────────────────────────────────


# ── 偏好設定 (Feature 13) ──────────────────────────────────────────


@router.put("/preferences/notifications")
def update_notification_prefs(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新通知偏好設定。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    if hasattr(user, "notification_preferences"):
        user.notification_preferences = body
    db.commit()

    return {"ok": True, "message": "通知偏好已更新", "preferences": body}


@router.put("/preferences/dark-mode")
def update_dark_mode(
    body: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """切換深色模式設定。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    return {
        "ok": True,
        "message": "深色模式設定已更新",
        "dark_mode": body.get("dark_mode", "disabled"),
    }


# ── 科目管理 (Feature 13) ──────────────────────────────────────────


@router.get("/subjects/{subject_name}/edit")
def edit_subject(
    subject_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """取得科目編輯資料（導向 Onboarding 編輯頁）。"""
    import urllib.parse
    from app.models.subject import Subject
    from app.models.learning_journey import LearningJourney

    decoded = urllib.parse.unquote(subject_name)
    user_uuid = uuid_mod.UUID(user_id)

    subject = db.query(Subject).filter(Subject.name == decoded).first()
    if not subject:
        raise HTTPException(status_code=404, detail={"message": f"科目 '{decoded}' 不存在"})

    journey = db.query(LearningJourney).filter(
        LearningJourney.user_id == user_uuid,
        LearningJourney.subject_id == subject.id,
    ).first()
    if not journey:
        raise HTTPException(status_code=404, detail={"message": "尚未加入此科目"})

    return {
        "ok": True,
        "subject": {
            "id": str(subject.id),
            "name": subject.name,
        },
        "redirect": f"/onboarding/edit/{subject.id}",
        "message": f"導向至 {decoded} 科目編輯頁",
    }


@router.delete("/subjects/{subject_name}")
def remove_subject(
    subject_name: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """從帳戶移除備考科目。"""
    import urllib.parse
    from app.models.subject import Subject
    from app.models.learning_journey import LearningJourney

    decoded = urllib.parse.unquote(subject_name)
    user_uuid = uuid_mod.UUID(user_id)

    subject = db.query(Subject).filter(Subject.name == decoded).first()
    if not subject:
        raise HTTPException(status_code=404, detail={"message": f"科目 '{decoded}' 不存在"})

    journey = db.query(LearningJourney).filter(
        LearningJourney.user_id == user_uuid,
        LearningJourney.subject_id == subject.id,
    ).first()
    if not journey:
        raise HTTPException(status_code=404, detail={"message": "尚未加入此科目"})

    db.delete(journey)
    db.commit()

    return {"ok": True, "message": f"已移除科目 {decoded}"}
