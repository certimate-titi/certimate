from behave import then


FIELD_MAP = {
    "email": "email",
    "訂閱方案": "subscription_plan",
    "角色": "role",
    "狀態": "status",
}


@then('回應中的使用者資訊應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()
    user_data = data.get("user", data)

    for row in context.table:
        field_name = row["欄位"]
        expected_value = row["值"]
        api_field = FIELD_MAP.get(field_name, field_name)

        actual_value = user_data.get(api_field)
        assert actual_value is not None, \
            f"回應中找不到欄位 '{api_field}': {user_data}"
        assert str(actual_value) == expected_value, \
            f"欄位 '{api_field}' 應為 '{expected_value}'，實際為 '{actual_value}'"
