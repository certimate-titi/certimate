"""Then FREE 方案的每月上傳數限額應為 — Aggregate Then"""

from behave import then

from app.models.plan_quota import PlanQuota


@then('{plan} 方案的每月上傳數限額應為 {expected:d}')
def step_impl(context, plan, expected):
    db = context.db_session
    db.expire_all()
    quota = db.query(PlanQuota).filter(PlanQuota.plan == plan).first()
    assert quota is not None, f"找不到 {plan} 方案的限額設定"
    assert quota.monthly_uploads == expected, \
        f"每月上傳數應為 {expected}，實際 {quota.monthly_uploads}"
