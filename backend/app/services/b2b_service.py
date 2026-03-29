"""B2B 機構管理 Service。"""

import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.institution import Institution


class B2BService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard(self, user_id: str):
        """取得機構管理後台資訊。"""
        user_uuid = uuid.UUID(user_id)
        user = self.db.query(User).filter_by(id=user_uuid).first()
        if not user:
            return {"error": True, "status_code": 404, "message": "使用者不存在"}

        plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
        role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        is_admin = role in ("admin", "super_admin", "ADMIN", "SUPER_ADMIN")

        if plan != "ULTRA" and not is_admin:
            return {"error": True, "status_code": 403, "message": "此功能僅限 ULTRA 方案用戶使用"}

        if role != "org_admin" and not is_admin:
            return {"error": True, "status_code": 403, "message": "您沒有機構管理員權限"}

        institution = self.db.query(Institution).filter_by(admin_user_id=user_uuid).first()
        if not institution:
            return {"error": True, "status_code": 404, "message": "找不到您管理的機構"}

        return {
            "institution_name": institution.name,
            "institution_id": str(institution.id),
        }
