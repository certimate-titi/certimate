"""14 天免費試用 Service。"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionPlan, SubscriptionStatus

TRIAL_DAYS = 14


class TrialService:
    def __init__(self, db: Session):
        self.db = db

    def start_trial(self, user_id: str) -> dict:
        """啟動 14 天 ULTRA 免費試用。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        # 檢查是否已使用過試用
        if user.has_used_trial:
            return {"error": True, "status_code": 400, "message": "您已使用過免費試用，請直接訂閱"}

        # 檢查是否已是 ULTRA
        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        if plan == "ULTRA":
            return {"error": True, "status_code": 400, "message": "您已是 ULTRA 方案用戶"}

        now = datetime.now(timezone.utc)

        # 儲存原方案，以便試用到期後恢復
        user.pre_trial_plan = plan
        user.subscription_plan = SubscriptionPlan.ULTRA
        user.subscription_status = SubscriptionStatus.TRIAL
        user.trial_start_date = now
        user.trial_end_date = now + timedelta(days=TRIAL_DAYS)
        user.has_used_trial = True

        self.db.commit()

        return {
            "trial_started": True,
            "trial_start": user.trial_start_date.isoformat(),
            "trial_end": user.trial_end_date.isoformat(),
            "remaining_days": TRIAL_DAYS,
        }

    def get_trial_status(self, user_id: str) -> dict:
        """查詢試用狀態。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        status = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)

        if status != "trial":
            return {
                "is_trial": False,
                "has_used_trial": user.has_used_trial,
            }

        now = datetime.now(timezone.utc)
        remaining = (user.trial_end_date - now).days if user.trial_end_date else 0
        remaining = max(0, remaining)

        return {
            "is_trial": True,
            "trial_start": user.trial_start_date.isoformat() if user.trial_start_date else None,
            "trial_end": user.trial_end_date.isoformat() if user.trial_end_date else None,
            "remaining_days": remaining,
            "has_used_trial": True,
        }

    def convert_to_paid(self, user_id: str) -> dict:
        """試用期間轉為正式付費。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        status = user.subscription_status.value if hasattr(user.subscription_status, 'value') else str(user.subscription_status)
        if status != "trial":
            return {"error": True, "status_code": 400, "message": "您目前不在試用期間"}

        user.subscription_status = SubscriptionStatus.ACTIVE
        user.trial_end_date = None
        user.pre_trial_plan = None
        self.db.commit()

        return {"message": "已成功轉為正式 ULTRA 方案", "plan": "ULTRA"}

    def check_and_expire_trials(self, current_date: datetime = None) -> dict:
        """檢查並過期已到期的試用用戶（由 scheduler 呼叫）。"""
        if current_date is None:
            current_date = datetime.now(timezone.utc)

        # Find all trial users whose trial has expired
        expired_users = (
            self.db.query(User)
            .filter(
                User.subscription_status == SubscriptionStatus.TRIAL,
                User.trial_end_date <= current_date,
            )
            .all()
        )

        expired_count = 0
        for user in expired_users:
            # Restore to pre-trial plan
            pre_plan = user.pre_trial_plan or "FREE"
            user.subscription_plan = SubscriptionPlan(pre_plan)
            user.subscription_status = SubscriptionStatus.ACTIVE
            user.pre_trial_plan = None
            expired_count += 1

        if expired_count > 0:
            self.db.commit()

        return {
            "checked_date": current_date.isoformat(),
            "expired_count": expired_count,
        }
