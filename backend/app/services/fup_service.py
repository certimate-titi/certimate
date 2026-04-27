"""FUP (Fair Use Policy) 軟上限 Service。"""

import uuid
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User, SubscriptionPlan
from app.models.ai_chat import AiChatSession as AiChat
from app.models.audit_log import AdminAuditLog

logger = logging.getLogger("certimate.fup")

DAILY_SOFT_CAP = 1000  # 每日 AI 呼叫軟上限
CONSECUTIVE_DAYS_THRESHOLD = 3  # 連續 N 天超過軟上限觸發管理員通知


class FUPService:
    """FUP Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def check_daily_usage(self, user_id: str) -> dict:
        """檢查用戶當日 AI 呼叫次數是否超��軟上限。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        if plan != "ULTRA":
            return {"fup_applicable": False, "message": "FUP 僅適用於 ULTRA 方案"}

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_count = (
            self.db.query(func.count(AiChat.id))
            .filter(
                AiChat.user_id == user_uuid,
                AiChat.created_at >= today_start,
            )
            .scalar() or 0
        )

        exceeded = daily_count >= DAILY_SOFT_CAP

        return {
            "fup_applicable": True,
            "daily_count": daily_count,
            "daily_soft_cap": DAILY_SOFT_CAP,
            "exceeded": exceeded,
            "warning_message": "您今日的使用量較高" if exceeded else None,
        }

    def run_daily_check(self) -> dict:
        """批次檢查所有 ULTRA 用戶的每日用量（由 scheduler 呼叫）。"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # 找出今日超過軟上限的 ULTRA 用戶
        exceeded_users = (
            self.db.query(
                AiChat.user_id,
                func.count(AiChat.id).label("count"),
            )
            .join(User, AiChat.user_id == User.id)
            .filter(
                User.subscription_plan == SubscriptionPlan.ULTRA,
                AiChat.created_at >= today_start,
            )
            .group_by(AiChat.user_id)
            .having(func.count(AiChat.id) >= DAILY_SOFT_CAP)
            .all()
        )

        exceeded_count = len(exceeded_users)

        # Check consecutive days via AdminAuditLog entries
        alerts = []
        consecutive_user_ids = self._find_consecutive_offenders()
        for user_id, days, email in consecutive_user_ids:
            alerts.append({
                "user_id": str(user_id),
                "email": email,
                "consecutive_days": days,
            })

        logger.info("FUP daily check: %d ULTRA users exceeded %d calls, %d consecutive alerts",
                     exceeded_count, DAILY_SOFT_CAP, len(alerts))

        return {
            "checked_date": today_start.isoformat(),
            "exceeded_users": exceeded_count,
            "soft_cap": DAILY_SOFT_CAP,
            "alerts": alerts,
        }

    def _find_consecutive_offenders(self) -> list:
        """Find users who triggered soft cap for N+ consecutive days."""
        # Query AdminAuditLog for fup_soft_cap_triggered entries
        logs = (
            self.db.query(AdminAuditLog)
            .filter(AdminAuditLog.action == "fup_soft_cap_triggered")
            .order_by(AdminAuditLog.created_at.desc())
            .all()
        )

        # Group by user
        user_logs = {}
        for log in logs:
            uid = log.target_id
            if uid not in user_logs:
                user_logs[uid] = []
            user_logs[uid].append(log.created_at)

        results = []
        for uid, dates in user_logs.items():
            # Count consecutive days (from most recent)
            sorted_dates = sorted(set(d.date() for d in dates), reverse=True)
            consecutive = 1
            for i in range(1, len(sorted_dates)):
                if (sorted_dates[i - 1] - sorted_dates[i]).days <= 1:
                    consecutive += 1
                else:
                    break

            if consecutive >= CONSECUTIVE_DAYS_THRESHOLD:
                user = self.db.query(User).filter_by(id=uid).first()
                email = user.email if user else "unknown"
                results.append((uid, consecutive, email))

        return results
