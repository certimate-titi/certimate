"""Then 回應應包含冷卻中用戶 — Readmodel Then"""

from behave import then


@then('回應應包含冷卻中用戶：')
def step_impl(context):
    data = context.last_response.json()
    cooling_users = data.get("cooling_users", [])

    for row in context.table:
        user_id_key = row["使用者 ID"].strip()
        email = row["Email"]
        reason = row["原因"]
        # We only check the user exists with expected email and reason;
        # cooldown seconds may vary by test execution time
        expected_user_id = context.ids.get(user_id_key)

        matched = None
        for cu in cooling_users:
            if cu.get("email") == email:
                matched = cu
                break

        assert matched is not None, \
            f"冷卻用戶清單中找不到 email={email}，實際: {cooling_users}"
        assert matched.get("reason") == reason, \
            f"用戶 {email} 的冷卻原因應為 '{reason}'，實際 '{matched.get('reason')}'"
