"""Then — 回應應包含各方案額度比較表。"""

from behave import then


@then('回應應包含各方案額度比較：')
def step_plan_comparison(context):
    response = context.last_response
    data = response.json()

    plans_data = data.get("plan_comparison", data.get("plans", []))

    for row in context.table:
        plan_name = row["方案"]
        matched = None
        for p in plans_data:
            if p.get("plan") == plan_name or p.get("name") == plan_name:
                matched = p
                break
        assert matched is not None, \
            f"方案 '{plan_name}' 不在比較表中，實際: {[p.get('plan', p.get('name')) for p in plans_data]}"
