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
    """查詢使用量摘要（legacy schema，保留向後相容）。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    usage = db.query(UserUsage).filter(UserUsage.user_id == user.id).first()

    return {
        "ok": True,
        "exams_used": usage.monthly_exams_used if usage else 0,
        "exams_limit": 10,
        "uploads_used": usage.monthly_uploads_used if usage else 0,
        "uploads_limit": 5,
        "documents_used": usage.monthly_uploads_used if usage else 0,
        "documents_limit": 5,
        "ai_chats_used": usage.daily_ai_chats_used if usage else 0,
        "ai_chats_limit": 3,
    }


@router.get("/quota-status")
def get_quota_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """統一配額狀態查詢 — 5 維度（uploads / exams / ai_chats / vision_pages / file_size）。

    Returns dict 含：
    - plan: 訂閱方案代號（FREE / PRO / PRO_PLUS / ULTRA / EDU / ADMIN_UNLIMITED）
    - is_unlimited: ADMIN / SUPER_ADMIN 為 True，永遠不被擋
    - quotas: 5 項配額狀態（已用 / 上限 / 期間 / 百分比 / 是否達上限）
    """
    from datetime import datetime, timezone
    from app.models.plan_quota import PlanQuota
    from app.models.user import UserRole

    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})

    # ADMIN / SUPER_ADMIN 視為無限制（與 frontend isAdmin 守門一致）
    is_admin = user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else user.subscription_plan
    plan_str = plan_val or "FREE"
    quota = db.query(PlanQuota).filter_by(plan=plan_str).first()

    # 取當月 user_usage（YYYY-MM）
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    usage = db.query(UserUsage).filter_by(user_id=user.id, period=period).first()

    def _build(used: int, limit: int | None, period_type: str, label: str, action_hint: str = ""):
        # is_unlimited admin override
        if is_admin or limit is None or limit < 0:
            return {
                "label": label,
                "used": used,
                "limit": -1,  # -1 表示無上限
                "remaining": -1,
                "percentage": 0,
                "is_warning": False,
                "is_blocked": False,
                "period": period_type,
                "action_hint": action_hint,
            }
        if limit == 0:
            return {
                "label": label,
                "used": used,
                "limit": 0,
                "remaining": 0,
                "percentage": 100,
                "is_warning": True,
                "is_blocked": True,
                "period": period_type,
                "action_hint": action_hint,
            }
        pct = round(min(100, (used / limit) * 100))
        return {
            "label": label,
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used),
            "percentage": pct,
            "is_warning": pct >= 80,
            "is_blocked": used >= limit,
            "period": period_type,
            "action_hint": action_hint,
        }

    quotas = {
        "monthly_uploads": _build(
            usage.monthly_uploads_used if usage else 0,
            quota.monthly_uploads if quota else None,
            "monthly", "資源上傳", "本月可上傳的學習資源檔案數",
        ),
        "monthly_exams": _build(
            usage.monthly_exams_used if usage else 0,
            quota.monthly_exams if quota else None,
            "monthly", "模擬測驗", "本月可發起的模擬機考次數",
        ),
        "daily_ai_chats": _build(
            usage.daily_ai_chats_used if usage else 0,
            quota.daily_ai_chats if quota else None,
            "daily", "AI 教練對話", "今日剩餘 AI 教練追問次數（每日重置）",
        ),
        "monthly_vision_pages": _build(
            usage.monthly_vision_pages_used if usage else 0,
            quota.monthly_vision_pages if quota else None,
            "monthly", "PDF / 圖像解析", "本月可被 AI 解析的 PDF / 圖像頁數",
        ),
        # file_size 是限制不是計數
        "max_file_size_mb": {
            "label": "單檔大小",
            "used": 0,
            "limit": -1 if is_admin else (quota.max_file_size_mb if quota else 10),
            "remaining": -1 if is_admin else (quota.max_file_size_mb if quota else 10),
            "percentage": 0,
            "is_warning": False,
            "is_blocked": False,
            "period": "constant",
            "action_hint": "單一上傳檔案的大小上限（MB）",
        },
    }

    return {
        "ok": True,
        "plan": "ADMIN_UNLIMITED" if is_admin else plan_str,
        "is_unlimited": is_admin,
        "period": period,
        "quotas": quotas,
        "upgrade_url": "/account",
        "pricing_url": "/pricing",
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

    if body.confirm_text not in ("確認刪除", "DELETE", "刪除我的帳號"):
        raise HTTPException(status_code=400, detail={"message": "確認文字不符"})

    from app.models.user import UserStatus
    user.status = UserStatus.DELETED
    db.commit()

    return {"ok": True, "message": "帳號已標記為刪除，將在 30 天後永久移除"}


@router.get("/notification-preferences")
def get_notification_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """讀取當前用戶的通知偏好設定（F22 / L81）。"""
    user = _get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    prefs = getattr(user, "notification_preferences", None) or {}
    return {"preferences": prefs}


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

    # Store preferences in dedicated JSON field (migration 076 added)
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
