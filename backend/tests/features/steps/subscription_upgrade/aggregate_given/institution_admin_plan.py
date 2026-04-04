"""Given 機構管理員訂閱方案 — Aggregate Given"""

import uuid

from behave import given

from app.models.institution import Institution
from app.models.user import User, SubscriptionPlan


_PLAN_MAP = {
    "FREE": SubscriptionPlan.FREE,
    "PRO_199": SubscriptionPlan.PRO,
    "PRO_PLUS_399": SubscriptionPlan.PRO_PLUS,
    "ULTRA_1599": SubscriptionPlan.ULTRA,
}


@given('機構 {inst_id:d} 的管理員訂閱方案為 "{plan}"')
def step_impl(context, inst_id, plan):
    db = context.db_session
    inst_uuid = uuid.UUID(int=inst_id)

    # Ensure institution exists
    inst = db.query(Institution).filter_by(id=inst_uuid).first()
    if inst is None:
        # Create a default institution with first available admin
        from app.models.user import UserRole
        admin = db.query(User).filter_by(role=UserRole.USER).first()
        if admin is None:
            admin = db.query(User).first()
        inst = Institution(
            id=inst_uuid,
            name=f"測試機構 {inst_id}",
            admin_user_id=admin.id,
        )
        db.add(inst)
        db.flush()
        context.ids[f"institution_{inst_id}"] = str(inst.id)

    # Update admin subscription plan
    admin_user = db.query(User).filter_by(id=inst.admin_user_id).first()
    assert admin_user is not None, f"找不到機構 {inst_id} 的管理員"
    admin_user.subscription_plan = _PLAN_MAP.get(plan, SubscriptionPlan.FREE)
    db.commit()

    context.memo[f"institution_{inst_id}_admin_email"] = admin_user.email
