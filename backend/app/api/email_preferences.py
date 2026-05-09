"""Email preferences API — Sprint 9 議題 E.

公開：
- POST /api/v1/email/unsubscribe  退訂連結（token-only auth）
- GET  /api/v1/email/preferences  讀偏好（JWT auth）
- PUT  /api/v1/email/preferences  改偏好（JWT auth）

Admin only：
- POST /api/v1/admin/retention/run-daily-cron  手動觸發 retention email batch
"""

import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db
from app.models.user import User, UserRole
from app.models.user_email_preferences import UserEmailPreferences
from app.services.retention_email_service import (
    RetentionEmailService,
    decode_unsubscribe_token,
    get_or_create_preferences,
)

router = APIRouter(prefix="/email", tags=["email"])
admin_router = APIRouter(prefix="/admin/retention", tags=["admin", "retention"])


# ── Public（token-only） ───────────────────────────────────────────────────

class UnsubscribeResponse(BaseModel):
    ok: bool
    trigger: str | None = None
    message: str


@router.get("/unsubscribe", response_model=UnsubscribeResponse)
def unsubscribe(
    token: str = Query(...),
    trigger: str | None = Query(None, description="daily_review | weekly_report | streak_warning | all"),
    db: Session = Depends(get_db),
):
    """點 email 內退訂連結，把對應 trigger 的 enabled 設 false。

    parse_failure 是事務型，無法退訂（API 拒絕）。
    """
    user_id = decode_unsubscribe_token(token)
    if user_id is None:
        raise HTTPException(status_code=400, detail={"message": "退訂連結無效或已過期"})

    pref = db.query(UserEmailPreferences).filter_by(user_id=user_id).first()
    if pref is None:
        raise HTTPException(status_code=404, detail={"message": "偏好不存在"})

    valid_triggers = {"daily_review", "weekly_report", "streak_warning", "all"}
    if trigger and trigger not in valid_triggers:
        raise HTTPException(status_code=400, detail={"message": "trigger 無效"})

    if trigger == "daily_review" or trigger == "all":
        pref.daily_review_enabled = False
    if trigger == "weekly_report" or trigger == "all":
        pref.weekly_report_enabled = False
    if trigger == "streak_warning" or trigger == "all":
        pref.streak_warning_enabled = False
    db.commit()
    return UnsubscribeResponse(ok=True, trigger=trigger or "all", message="已成功退訂")


# ── 用戶讀寫自己的 preferences（JWT auth） ─────────────────────────────────

class PreferencesPayload(BaseModel):
    daily_review_enabled: bool | None = None
    weekly_report_enabled: bool | None = None
    streak_warning_enabled: bool | None = None


@router.get("/preferences")
def get_my_preferences(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    pref = get_or_create_preferences(db, user)
    db.commit()
    return {
        "daily_review_enabled": pref.daily_review_enabled,
        "weekly_report_enabled": pref.weekly_report_enabled,
        "streak_warning_enabled": pref.streak_warning_enabled,
        "parse_failure_enabled": True,  # 事務型固定 true
    }


@router.put("/preferences")
def update_my_preferences(
    body: PreferencesPayload,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail={"message": "使用者不存在"})
    pref = get_or_create_preferences(db, user)
    if body.daily_review_enabled is not None:
        pref.daily_review_enabled = body.daily_review_enabled
    if body.weekly_report_enabled is not None:
        pref.weekly_report_enabled = body.weekly_report_enabled
    if body.streak_warning_enabled is not None:
        pref.streak_warning_enabled = body.streak_warning_enabled
    db.commit()
    return {"ok": True}


# ── Admin: cron 觸發入口 ───────────────────────────────────────────────────

@admin_router.get("/analytics")
def get_retention_analytics(
    days: int = Query(30, ge=1, le=90),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """retention email 寄送分析（近 N 天）— 補配 UTM 參數讓你雙向對帳。

    回傳 by trigger × variant × status 的彙總，配合 GA / PostHog 的 utm_campaign
    + utm_content 拉訪客行為，可算出每個 trigger 的「寄送 → click → conversion」漏斗。

    回傳結構：
      {
        "days": 30,
        "summary": [{
          "trigger_id": "daily_review",
          "variant": "A",
          "sent": 120, "skipped": 30, "failed": 2,
          "skipped_breakdown": {"FREE_NOT_ELIGIBLE": 20, "ALREADY_SENT_TODAY": 10}
        }, ...]
      }
    """
    from sqlalchemy import text
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})

    rows = db.execute(
        text(
            """
            SELECT
              trigger_id,
              COALESCE(subject_variant, 'A') AS variant,
              status,
              reason,
              COUNT(*) AS n
            FROM email_send_log
            WHERE sent_at >= NOW() - (:days || ' days')::interval
            GROUP BY trigger_id, COALESCE(subject_variant, 'A'), status, reason
            ORDER BY trigger_id, variant, status
            """
        ),
        {"days": days},
    ).fetchall()

    # 折成 (trigger, variant) → counts 結構
    bucket: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r[0], r[1])
        b = bucket.setdefault(key, {"sent": 0, "skipped": 0, "failed": 0,
                                    "skipped_breakdown": {}, "failed_breakdown": {}})
        st = r[2]
        n = int(r[4])
        if st == "sent":
            b["sent"] += n
        elif st == "skipped":
            b["skipped"] += n
            if r[3]:
                b["skipped_breakdown"][r[3]] = b["skipped_breakdown"].get(r[3], 0) + n
        elif st == "failed":
            b["failed"] += n
            if r[3]:
                b["failed_breakdown"][r[3]] = b["failed_breakdown"].get(r[3], 0) + n

    summary = [
        {"trigger_id": k[0], "variant": k[1], **v}
        for k, v in bucket.items()
    ]
    return {"days": days, "summary": summary}


@admin_router.post("/run-daily-cron")
def run_daily_cron(
    background_tasks: BackgroundTasks,
    trigger: str = Query("daily_review", description="daily_review (MVP only)"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """手動觸發 retention email batch。

    Sprint 9 MVP：僅實作 daily_review。weekly_report / streak_warning /
    parse_failure 留給後續 sprint（資料源已備好但 batch 邏輯未寫）。

    生產環境應由 Cloud Scheduler 每天 08:00 TW 呼叫此端點。
    """
    user = db.query(User).filter_by(id=uuid.UUID(user_id)).first()
    if not user or user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail={"message": "需要 SUPER_ADMIN 權限"})

    if trigger != "daily_review":
        raise HTTPException(status_code=400, detail={
            "message": f"trigger '{trigger}' 尚未實作（MVP 僅 daily_review）"
        })

    svc = RetentionEmailService(db)
    summary = svc.run_daily_review_batch()
    return summary
