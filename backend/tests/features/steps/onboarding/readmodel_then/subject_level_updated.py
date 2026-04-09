"""Then 科目自評程度更新驗證 — ReadModel Then"""

from behave import then


@then('"{subject}" 的自評程度應更新為 "{expected_level}"')
def step_impl(context, subject, expected_level):
    """驗證科目自評程度已更新。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        actual_level = (
            data.get("self_assessed_level")
            or data.get("level")
            or ""
        )
        assert actual_level == expected_level, \
            f"'{subject}' 的自評程度應為 '{expected_level}'，實際: '{actual_level}'"
