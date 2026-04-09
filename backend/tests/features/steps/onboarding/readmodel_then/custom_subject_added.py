"""Then 自訂科目相關斷言 — ReadModel Then"""

from behave import then


@then('已選科目列表應包含 "{subject}"')
def step_impl_selected_contains(context, subject):
    """驗證已選科目列表包含指定科目。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        subjects = data if isinstance(data, list) else data.get("subjects", [data])
        names = [s.get("subject_name") or s.get("name") or "" for s in subjects]
        assert subject in names, \
            f"已選科目列表應包含 '{subject}'，實際: {names}"


@then('該科目應標記為「自訂科目」')
def step_impl_marked_custom(context):
    """驗證科目被標記為自訂。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        is_custom = data.get("is_custom", False)
        assert is_custom, \
            f"科目應標記為自訂，但 is_custom={is_custom}"
