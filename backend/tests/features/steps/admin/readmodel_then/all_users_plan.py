"""Then 回應中所有使用者的方案應為 — Read Model Then"""

from behave import then


@then('回應中所有使用者的方案應為 "{expected_plan}"')
def step_impl(context, expected_plan):
    response = context.last_response
    data = response.json()
    users = data.get("users", [])

    assert len(users) > 0, "回應中沒有使用者"
    for u in users:
        actual = u.get("plan")
        assert actual == expected_plan, \
            f"使用者 {u.get('email')} 的方案應為 '{expected_plan}'，實際為 '{actual}'"
