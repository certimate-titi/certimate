"""Then 回應應包含使用者摘要資訊 — Read Model Then"""

from behave import then


@then('回應應包含使用者 "{email}" 的摘要資訊：')
def step_impl(context, email):
    response = context.last_response
    data = response.json()
    users = data.get("users", [])

    # Find user with matching email
    matched = next((u for u in users if u.get("email") == email), None)
    assert matched is not None, \
        f"回應中找不到 email='{email}' 的使用者，users={users}"

    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        actual = matched.get(field)
        assert str(actual) == str(expected), \
            f"使用者 {email} 的 {field} 應為 '{expected}'，實際為 '{actual}'"
