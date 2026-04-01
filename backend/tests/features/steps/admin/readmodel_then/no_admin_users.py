"""Then 回應不應包含角色為 admin 或 super_admin 的使用者 — Read Model Then"""

from behave import then


@then('回應不應包含角色為 "{role1}" 或 "{role2}" 的使用者')
def step_impl(context, role1, role2):
    response = context.last_response
    data = response.json()
    users = data.get("users", [])

    for u in users:
        user_role = u.get("role", "")
        assert user_role != role1 and user_role != role2, \
            f"回應包含角色為 '{user_role}' 的使用者 {u.get('email')}，不應出現"
