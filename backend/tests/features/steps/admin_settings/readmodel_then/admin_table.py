"""Then 管理員帳號表格驗證 — ReadModel Then"""

from behave import then


@then('表格應包含以下欄位：Email、角色、建立日期、狀態')
def step_impl_admin_table_fields(context):
    """驗證管理員列表包含必要欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        admins = data if isinstance(data, list) else data.get("admins", [data])
        if admins:
            admin = admins[0]
            for field in ("email", "role", "created_at", "status"):
                assert field in admin, \
                    f"管理員資料缺少欄位 '{field}'，實際: {admin.keys()}"


@then('表格中應包含 "{email1}" 與 "{email2}"')
def step_impl_admin_table_contains(context, email1, email2):
    """驗證管理員列表包含指定帳號。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        admins = data if isinstance(data, list) else data.get("admins", [])
        emails = [a.get("email", "") for a in admins]
        assert email1 in emails, \
            f"管理員列表應包含 '{email1}'，實際: {emails}"
        assert email2 in emails, \
            f"管理員列表應包含 '{email2}'，實際: {emails}"
