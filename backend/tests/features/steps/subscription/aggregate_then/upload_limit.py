"""Then — 驗證使用者每月上傳限額。"""

import uuid

from behave import then

from app.models.plan_quota import PlanQuota
from app.models.user import User

# DB plan name -> PlanQuota plan name
_DB_TO_QUOTA = {
    "FREE": "FREE",
    "PRO": "PRO_199",
    "PRO_PLUS": "PRO_PLUS_399",
    "ULTRA": "ULTRA_1599",
    "EDU": "EDU",
}


@then('使用者 "{email}" 的每月上傳限額應為 {count:d}')
def step_upload_limit(context, email, count):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    db.refresh(user)
    plan = user.subscription_plan.value if hasattr(user.subscription_plan, 'value') else str(user.subscription_plan)

    # Try both DB name and display name for PlanQuota lookup
    quota_plan = _DB_TO_QUOTA.get(plan, plan)
    quota = db.query(PlanQuota).filter_by(plan=quota_plan).first()
    if quota is None:
        quota = db.query(PlanQuota).filter_by(plan=plan).first()
    assert quota is not None, f"找不到方案 '{plan}' / '{quota_plan}' 的額度設定"
    assert quota.monthly_uploads == count, \
        f"預期每月上傳限額 {count}，實際 {quota.monthly_uploads}"
