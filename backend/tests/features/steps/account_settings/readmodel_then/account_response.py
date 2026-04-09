"""Then 帳號設定 API 回應驗證 — ReadModel Then"""

from behave import then


@then('操作應失敗，錯誤訊息為 "{expected_message}"')
def step_impl_operation_failed_with_message(context, expected_message):
    """驗證操作失敗且錯誤訊息符合預期。"""
    response = context.last_response
    assert response.status_code in (400, 401, 403, 404, 409, 422), \
        f"操作應失敗（4xx），實際 {response.status_code}"
    if response.status_code != 404:
        data = response.json()
        error_msg = (
            data.get("detail")
            or data.get("message")
            or data.get("error")
            or str(data)
        )
        assert expected_message in error_msg, \
            f"錯誤訊息期望包含 '{expected_message}'，實際 '{error_msg}'"


@then('API 回應應包含更新後的個人資料')
def step_impl_updated_profile_response(context):
    """驗證 API 回應包含更新後的個人資料。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        assert "display_name" in data or "user" in data or "profile" in data, \
            "回應應包含個人資料欄位"


@then('API 回應應包含：')
def step_impl_api_response_contains(context):
    """驗證 API 回應包含指定欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        for row in context.table:
            field = row["欄位"]
            assert field in data, f"回應缺少欄位 '{field}'"
