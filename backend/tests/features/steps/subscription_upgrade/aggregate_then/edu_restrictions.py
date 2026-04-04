"""Then EDU 學生限制 — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User
from app.models.plan_quota import PlanQuota


_USER_PLAN_MAP = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
    "EDU": "EDU",
}


@then('使用者 "{email}" 不可上傳資源')
def step_impl_no_upload(context, email):
    db = context.db_session
    db.expire_all()
    if email in context.ids:
        user_uuid = uuid.UUID(context.ids[email])
        user = db.query(User).filter_by(id=user_uuid).first()
    else:
        user = db.query(User).filter_by(email=email).first()
    assert user is not None, f"找不到使用者 '{email}'"

    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    plan_key = _USER_PLAN_MAP.get(plan_val, plan_val)

    quota = db.query(PlanQuota).filter_by(plan=plan_key).first()
    assert quota is not None, f"找不到方案 '{plan_key}' 的配額設定"
    assert quota.monthly_uploads == 0, (
        f"EDU 學生不應有上傳配額，實際 {quota.monthly_uploads}"
    )


@then('使用者 "{email}" 不可自主出題')
def step_impl_no_exam(context, email):
    db = context.db_session
    db.expire_all()
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    assert user is not None, f"找不到使用者 '{email}'"

    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    # EDU 學生使用機構提供的考題，不可自主出題
    # 驗證使用者為 EDU 方案（EDU 學生的考試由機構管理）
    assert plan_val == "EDU", (
        f"預期方案為 EDU 以限制自主出題，實際方案 '{plan_val}'"
    )
