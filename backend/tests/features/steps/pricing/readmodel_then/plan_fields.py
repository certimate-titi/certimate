"""Then 每個方案應包含 — ReadModel Then"""

from behave import then


@then('每個方案應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    plans = data.get("plans", [])
    required_fields = [row["欄位"] for row in context.table]

    for plan in plans:
        for field in required_fields:
            assert field in plan, (
                f"方案 '{plan.get('plan_name')}' 缺少欄位 '{field}'"
            )
