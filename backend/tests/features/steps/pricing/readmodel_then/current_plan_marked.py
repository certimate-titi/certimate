"""Then PRO_199 方案應標記為目前方案 — ReadModel Then"""

from behave import then


@then('PRO_199 方案應標記為「目前方案」')
def step_impl(context):
    response = context.last_response
    data = response.json()

    plans = data.get("plans", [])
    pro_plan = next((p for p in plans if p.get("plan_name") == "PRO_199"), None)
    assert pro_plan is not None, "找不到 PRO_199 方案"
    assert pro_plan.get("is_current") is True, (
        f"PRO_199 應標記為目前方案，但 is_current={pro_plan.get('is_current')}"
    )
