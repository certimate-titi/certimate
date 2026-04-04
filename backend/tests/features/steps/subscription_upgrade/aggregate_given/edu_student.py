"""Given 使用者目前為機構的 EDU 學生 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User, SubscriptionPlan, SubscriptionStatus, UserRole
from app.models.institution import Institution


@given('使用者 "{email}" 目前為機構 {inst_id:d} 的 EDU 學生')
def step_impl(context, email, inst_id):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])
    inst_uuid = uuid.UUID(int=inst_id)

    # Ensure institution exists
    inst = db.query(Institution).filter_by(id=inst_uuid).first()
    if inst is None:
        admin = db.query(User).first()
        inst = Institution(
            id=inst_uuid,
            name=f"測試機構 {inst_id}",
            admin_user_id=admin.id,
        )
        db.add(inst)
        db.flush()
        context.ids[f"institution_{inst_id}"] = str(inst.id)

    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 '{email}'"

    user.subscription_plan = SubscriptionPlan.EDU
    user.subscription_status = SubscriptionStatus.ACTIVE
    user.role = UserRole.STUDENT
    user.org_id = inst_uuid
    db.commit()
