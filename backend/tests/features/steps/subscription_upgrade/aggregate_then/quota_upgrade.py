"""Then 使用者的限額應從 N 提升至 N — Aggregate Then"""

import uuid

from behave import then

from app.models.user import User
from app.models.plan_quota import PlanQuota


_PLAN_MAP = {
    "FREE": "FREE",
    "PRO_199": "PRO_199",
    "PRO_PLUS_399": "PRO_PLUS_399",
    "ULTRA_1599": "ULTRA_1599",
}

_USER_PLAN_MAP = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
}


def _get_user_plan_quota(db, email, context):
    """取得使用者目前方案的配額。"""
    user_uuid = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_uuid).first()
    plan_val = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)
    plan_key = _USER_PLAN_MAP.get(plan_val, plan_val)
    quota = db.query(PlanQuota).filter_by(plan=plan_key).first()
    return quota


@then('使用者 "{email}" 的每日 AI 對話限額應從 {old:d} 提升至 {new:d}')
def step_impl_ai(context, email, old, new):
    db = context.db_session
    db.expire_all()
    quota = _get_user_plan_quota(db, email, context)
    assert quota is not None, "找不到使用者目前方案的配額設定"
    actual = quota.daily_ai_chats
    assert actual == new, (
        f"預期每日 AI 對話限額 {new}，實際 {actual}"
    )


@then('使用者 "{email}" 的每月上傳限額應從 {old:d} 提升至 {new:d}')
def step_impl_upload(context, email, old, new):
    db = context.db_session
    db.expire_all()
    quota = _get_user_plan_quota(db, email, context)
    assert quota is not None, "找不到使用者目前方案的配額設定"
    actual = quota.monthly_uploads
    assert actual == new, (
        f"預期每月上傳限額 {new}，實際 {actual}"
    )


@then('使用者 "{email}" 的每月考試限額應從 {old:d} 提升至 {new:d}')
def step_impl_exam(context, email, old, new):
    db = context.db_session
    db.expire_all()
    quota = _get_user_plan_quota(db, email, context)
    assert quota is not None, "找不到使用者目前方案的配額設定"
    actual = quota.monthly_exams
    assert actual == new, (
        f"預期每月考試限額 {new}，實際 {actual}"
    )
