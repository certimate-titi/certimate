"""Pricing Service — 定價比較頁與升級引導。"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.plan_quota import PlanQuota
from app.models.user import User
from app.models.user_usage import UserUsage


PLAN_DB_TO_DISPLAY = {
    "FREE": "FREE", "PRO": "PRO_199", "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599", "EDU": "EDU",
}

PLAN_ORDER = ["FREE", "PRO_199", "PRO_PLUS_399", "ULTRA_1599"]

PLAN_FEES = {
    "FREE": 0, "PRO_199": 199, "PRO_PLUS_399": 399, "ULTRA_1599": 1599,
}

PLAN_FEATURES = {
    "FREE": ["AI 對話 3 次/日", "上傳 5 次/月", "考試 10 次/月", "自主出題"],
    "PRO_199": ["AI 對話 30 次/日", "上傳 50 次/月", "考試 100 次/月", "自主出題"],
    "PRO_PLUS_399": ["AI 對話 200 次/日", "上傳 200 次/月", "考試 500 次/月",
                      "Vision OCR 50 頁/月", "高階教練", "自主出題"],
    "ULTRA_1599": ["AI 對話無限", "上傳無限", "考試無限",
                    "Vision OCR 500 頁/月", "高階教練", "自主出題"],
}

# Upgrade path: from -> to
UPGRADE_PATH = {
    "FREE": "PRO_199",
    "PRO_199": "PRO_PLUS_399",
    "PRO_PLUS_399": "ULTRA_1599",
}


class PricingService:
    """Pricing Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db

    def get_pricing(self, user_id: str | None = None) -> dict:
        """Get pricing comparison page data."""
        # Determine current plan and trial eligibility
        current_plan = None
        has_used_trial = False

        if user_id:
            uid = uuid.UUID(user_id)
            user = self.db.query(User).filter_by(id=uid).first()
            if user:
                plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
                current_plan = PLAN_DB_TO_DISPLAY.get(plan_val, plan_val)
                has_used_trial = bool(user.has_used_trial) if hasattr(user, 'has_used_trial') else False

        plans = []
        for plan_name in PLAN_ORDER:
            plan_data = {
                "plan_name": plan_name,
                "monthly_fee": PLAN_FEES[plan_name],
                "features": PLAN_FEATURES.get(plan_name, []),
                "is_popular": plan_name == "PRO_PLUS_399",
                "is_current": plan_name == current_plan if current_plan else False,
            }

            # Determine CTA text
            if current_plan and plan_name == current_plan:
                plan_data["cta_text"] = "目前方案"
            elif plan_name == "ULTRA_1599" and not has_used_trial:
                plan_data["cta_text"] = "免費試用 14 天"
            elif current_plan and PLAN_ORDER.index(plan_name) > PLAN_ORDER.index(current_plan):
                plan_data["cta_text"] = "升級"
            elif not current_plan:
                plan_data["cta_text"] = "開始使用" if plan_name == "FREE" else "訂閱"
            else:
                plan_data["cta_text"] = "降級"

            plans.append(plan_data)

        edu_section = {
            "title": "教育機構方案",
            "description": "ULTRA 方案含 30 名學生，適合補習班與老師",
            "cta_text": "聯絡我們",
        }

        return {
            "plans": plans,
            "edu_section": edu_section,
        }

    def check_upload_limit(self, user_id: str) -> dict:
        """Check if user has reached upload limit."""
        uid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        plan_display = PLAN_DB_TO_DISPLAY.get(plan_val, plan_val)

        quota = self.db.query(PlanQuota).filter_by(plan=plan_display).first()
        if not quota:
            quota = self.db.query(PlanQuota).filter_by(plan=plan_val).first()

        limit = quota.monthly_uploads if quota else 5
        if limit is None:
            # Unlimited
            return {"error": False, "allowed": True}

        period = datetime.now().strftime("%Y-%m")
        usage = self.db.query(UserUsage).filter_by(user_id=uid, period=period).first()
        used = usage.monthly_uploads_used if usage else 0

        if used >= limit:
            upgrade_to = UPGRADE_PATH.get(plan_display)
            upgrade_quota = None
            upgrade_fee = None
            if upgrade_to:
                uq = self.db.query(PlanQuota).filter_by(plan=upgrade_to).first()
                upgrade_quota = uq.monthly_uploads if uq else None
                upgrade_fee = PLAN_FEES.get(upgrade_to)

            result = {
                "error": True, "status_code": 400,
                "message": "已達本月上傳上限",
                "upgrade_guidance": {
                    "current_plan": plan_display,
                    "limit_type": "monthly_uploads",
                    "current_limit": limit,
                },
            }
            if upgrade_to:
                result["upgrade_guidance"]["upgrade_to"] = upgrade_to
                result["upgrade_guidance"]["upgrade_limit"] = upgrade_quota
                result["upgrade_guidance"]["monthly_fee"] = upgrade_fee
            return result

        return {"error": False, "allowed": True}

    def check_feature_access(self, user_id: str, feature: str) -> dict:
        """Check if user can access a premium feature."""
        uid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=uid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

        feature_requirements = {
            "coach": {"required_plan": "PRO_PLUS_399", "min_plans": ["PRO_PLUS", "ULTRA"],
                      "name": "高階教練", "message": "高階教練為 PRO_PLUS 以上方案專屬功能"},
            "edu_admin": {"required_plan": "ULTRA_1599", "min_plans": ["ULTRA"],
                          "name": "教育管理後台", "message": "此功能僅限 ULTRA 方案用戶使用"},
        }

        req = feature_requirements.get(feature)
        if not req:
            return {"error": True, "status_code": 404, "message": "功能不存在"}

        if plan_val not in req["min_plans"]:
            has_used_trial = bool(user.has_used_trial) if hasattr(user, 'has_used_trial') else False
            result = {
                "error": True, "status_code": 403,
                "message": req["message"],
                "upgrade_guidance": {
                    "required_plan": req["required_plan"],
                    "feature_name": req["name"],
                },
            }
            if req["required_plan"] == "ULTRA_1599":
                result["upgrade_guidance"]["trial_available"] = not has_used_trial
            return result

        return {"error": False, "allowed": True}
