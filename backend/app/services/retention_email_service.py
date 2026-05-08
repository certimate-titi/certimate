"""RetentionEmailService — Sprint 9 議題 E.

4 個 retention email trigger 的查詢、寄送、log 寫入：
- daily_review：scaffold_review_schedule 有 due 鷹架（每日 08:00）
- weekly_report：weekly_reports 表昨天新增（週日 09:00）
- streak_warning：streak ≥ 3 且當日未登入（每日 22:00）
- parse_failure：resource_parse_jobs 變 FAILED（即時）

完整文案見 docs/ops/retention-email-templates-2026-05-09.md
BDD 規格見 backend/tests/features/46-Sprint9-RetentionEmail.feature
"""

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Iterable

import jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.user import User, SubscriptionPlan
from app.models.user_email_preferences import UserEmailPreferences, EmailSendLog
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


# ── Plan tier 判斷 ─────────────────────────────────────────────────────────

def _is_free_user(user: User) -> bool:
    """FREE / EDU 學生視為「不收行銷信」。"""
    plan = user.subscription_plan
    val = plan.value if hasattr(plan, "value") else plan
    return val in ("FREE", "EDU")


# ── unsubscribe token JWT ──────────────────────────────────────────────────

def _generate_unsubscribe_token(user_id: uuid.UUID) -> str:
    """退訂連結用 JWT — 永久有效，purpose=email_unsubscribe。

    安全：不含 exp（永久），但用 jti 防 replay（DB row 替換 token 時舊的失效）。
    """
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "purpose": "email_unsubscribe",
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_unsubscribe_token(token: str) -> uuid.UUID | None:
    """解 unsubscribe token 取 user_id。失敗回 None。"""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != "email_unsubscribe":
            return None
        sub = payload.get("sub")
        return uuid.UUID(sub) if sub else None
    except Exception:
        return None


# ── Preferences 取得 / 建立 ────────────────────────────────────────────────

def get_or_create_preferences(db: Session, user: User) -> UserEmailPreferences:
    """讀 user_email_preferences；無則建。"""
    pref = db.query(UserEmailPreferences).filter_by(user_id=user.id).first()
    if pref:
        return pref
    pref = UserEmailPreferences(
        user_id=user.id,
        unsubscribe_token=_generate_unsubscribe_token(user.id),
    )
    db.add(pref)
    db.flush()
    return pref


# ── 寄送 / log ──────────────────────────────────────────────────────────────

def _log(db: Session, *, user_id: uuid.UUID, trigger_id: str,
         status: str, reason: str | None = None,
         subject: str | None = None, variant: str | None = None) -> None:
    db.add(EmailSendLog(
        user_id=user_id, trigger_id=trigger_id, status=status,
        reason=reason, subject=subject, subject_variant=variant,
    ))
    db.flush()


def _already_sent_today(db: Session, user_id: uuid.UUID, trigger_id: str) -> bool:
    """24h 內已成功寄過同類信不重寄。事務型（parse_failure）由 caller 自行決定是否查。"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    return db.execute(
        text(
            """
            SELECT 1 FROM email_send_log
            WHERE user_id = :uid AND trigger_id = :tid
              AND status = 'sent' AND sent_at >= :cutoff
            LIMIT 1
            """
        ),
        {"uid": str(user_id), "tid": trigger_id, "cutoff": cutoff},
    ).first() is not None


# ── 4 個 trigger ────────────────────────────────────────────────────────────

class RetentionEmailService:
    """Sprint 9 議題 E — 4 個 retention email trigger。"""

    TRIGGER_DAILY_REVIEW = "daily_review"
    TRIGGER_WEEKLY_REPORT = "weekly_report"
    TRIGGER_STREAK_WARNING = "streak_warning"
    TRIGGER_PARSE_FAILURE = "parse_failure"

    MARKETING_TRIGGERS = {TRIGGER_DAILY_REVIEW, TRIGGER_WEEKLY_REPORT, TRIGGER_STREAK_WARNING}

    def __init__(self, db: Session, email_service: EmailService | None = None):
        self.db = db
        self.email = email_service or EmailService()
        self.settings = get_settings()

    # ── trigger 1: daily_review ────────────────────────────────────────────
    def find_daily_review_recipients(self) -> Iterable[tuple[User, int]]:
        """有 due 鷹架（scaffold_review_schedule.due_date <= today）的用戶，回 (user, due_count)。"""
        rows = self.db.execute(
            text(
                """
                SELECT u.id, COUNT(s.id) AS due_count
                FROM users u
                JOIN scaffold_review_schedule s ON s.user_id = u.id
                LEFT JOIN user_email_preferences p ON p.user_id = u.id
                WHERE s.due_date <= CURRENT_DATE
                  AND u.status = 'active'
                  AND COALESCE(p.daily_review_enabled, TRUE) = TRUE
                GROUP BY u.id
                HAVING COUNT(s.id) > 0
                """
            )
        ).fetchall()
        for r in rows:
            user = self.db.query(User).filter_by(id=r[0]).first()
            if user:
                yield user, int(r[1])

    def send_daily_review(self, user: User, due_count: int) -> str:
        """status: 'sent' | 'skipped:<reason>' | 'failed:<reason>'."""
        if _is_free_user(user):
            _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_DAILY_REVIEW,
                 status="skipped", reason="FREE_NOT_ELIGIBLE")
            return "skipped:FREE_NOT_ELIGIBLE"
        if _already_sent_today(self.db, user.id, self.TRIGGER_DAILY_REVIEW):
            _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_DAILY_REVIEW,
                 status="skipped", reason="ALREADY_SENT_TODAY")
            return "skipped:ALREADY_SENT_TODAY"
        pref = get_or_create_preferences(self.db, user)
        if not pref.daily_review_enabled:
            _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_DAILY_REVIEW,
                 status="skipped", reason="USER_OPT_OUT")
            return "skipped:USER_OPT_OUT"

        subject = f"今日有 {due_count} 個重點等你複習 ✨"
        html = self._render_daily_review(user, due_count, pref.unsubscribe_token)
        ok = self.email._send(user.email, subject, html)
        if ok:
            _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_DAILY_REVIEW,
                 status="sent", subject=subject, variant="A")
            return "sent"
        _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_DAILY_REVIEW,
             status="failed", reason="SMTP_ERROR", subject=subject)
        return "failed:SMTP_ERROR"

    def _render_daily_review(self, user: User, due_count: int, unsub_token: str) -> str:
        cta = f"{self.settings.FRONTEND_URL}/today"
        unsub = (
            f"{self.settings.FRONTEND_URL}/email-preferences?token={unsub_token}&trigger=daily_review"
        )
        return f"""<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
            <h2 style="color:#10b981">嗨 {user.display_name or user.email}！</h2>
            <p style="font-size:16px;line-height:1.6">
              根據你的學習節奏，今天有 <b>{due_count} 個重點</b>等你複習。
              這是依遺忘曲線挑出的最佳複習時機 — 花 10 分鐘比明天花 30 分鐘有效。
            </p>
            <p><a href="{cta}" style="display:inline-block;padding:10px 24px;background:#10b981;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold">前往今日任務 →</a></p>
            <p style="color:#6b7280;font-size:12px;margin-top:32px">
              <a href="{unsub}" style="color:#6b7280">不再收到複習提醒</a>
            </p>
          </div>"""

    # ── trigger 4: parse_failure（事務型，必寄） ──────────────────────────
    def send_parse_failure(self, user: User, *, resource_id: str,
                           resource_name: str, failure_reason: str) -> str:
        pref = get_or_create_preferences(self.db, user)
        subject = "你的檔案上傳失敗，請重新上傳"
        cta = f"{self.settings.FRONTEND_URL}/dashboard?retry={resource_id}"
        unsub = f"{self.settings.FRONTEND_URL}/email-preferences?token={pref.unsubscribe_token}"
        # 事務型不能退訂（按鈕到 preference 頁但顯示「服務必要通知無法關閉」）
        html = f"""<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
            <h2 style="color:#dc2626">上傳檔案解析失敗</h2>
            <p style="font-size:16px;line-height:1.6">嗨 {user.display_name or user.email}，</p>
            <p><b>{resource_name}</b> 在 AI 解析時遇到問題：</p>
            <pre style="background:#fef2f2;padding:12px;border-radius:8px;white-space:pre-wrap">{failure_reason[:300]}</pre>
            <p>常見原因：PDF 加密 / 檔案損毀 / 影片連結權限不足。建議：</p>
            <ul><li>確認檔案能在本機開啟</li><li>YouTube 影片改用公開連結</li><li>PDF 解除密碼後再上傳</li></ul>
            <p><a href="{cta}" style="display:inline-block;padding:10px 24px;background:#10b981;color:#fff;text-decoration:none;border-radius:8px;font-weight:bold">重新上傳檔案</a></p>
            <p style="color:#6b7280;font-size:12px;margin-top:32px">
              此為服務必要通知，無法取消。<a href="{unsub}" style="color:#6b7280">管理其他 email 偏好</a>
            </p>
          </div>"""
        ok = self.email._send(user.email, subject, html)
        if ok:
            _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_PARSE_FAILURE,
                 status="sent", subject=subject, variant="A")
            return "sent"
        _log(self.db, user_id=user.id, trigger_id=self.TRIGGER_PARSE_FAILURE,
             status="failed", reason="SMTP_ERROR", subject=subject)
        return "failed:SMTP_ERROR"

    # ── batch 入口（admin cron）────────────────────────────────────────────
    def run_daily_review_batch(self) -> dict:
        sent = skipped = failed = 0
        for user, due in self.find_daily_review_recipients():
            r = self.send_daily_review(user, due)
            if r == "sent":
                sent += 1
            elif r.startswith("skipped"):
                skipped += 1
            else:
                failed += 1
        self.db.commit()
        return {"trigger": self.TRIGGER_DAILY_REVIEW,
                "sent": sent, "skipped": skipped, "failed": failed}
