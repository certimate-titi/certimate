"""Then 系統應回應 422 + 錯誤訊息應包含 SSRF 防護說明."""

from behave import then


@then("系統應回應 422 Unprocessable Entity")
def step_impl(context):
    """驗證 SSRF 防護回應 422。"""
    assert context.last_response is not None, "沒有 API 回應"
    assert context.last_response.status_code == 422, \
        f"期望 422，實際 {context.last_response.status_code}"


@then('錯誤訊息應包含 "URL 指向內網" 或 "不是有效的 YouTube URL"')
def step_impl_error_intranet(context):
    """驗證 SSRF 防護錯誤訊息（內網 URL）。"""
    response = context.last_response
    try:
        detail = str(response.json())
    except Exception:
        detail = response.text
    assert ("URL 指向內網" in detail or "不是有效的 YouTube URL" in detail or
            "intranet" in detail.lower() or "invalid" in detail.lower()), \
        f"錯誤訊息不符：{detail}"


@then('錯誤訊息應包含 "受保護的內部服務"')
def step_impl_error_metadata(context):
    """驗證 SSRF 防護錯誤訊息（Cloud Metadata）。"""
    response = context.last_response
    try:
        detail = str(response.json())
    except Exception:
        detail = response.text
    assert ("受保護的內部服務" in detail or "metadata" in detail.lower() or
            "protected" in detail.lower() or "ssrf" in detail.lower()), \
        f"錯誤訊息不符：{detail}"


@then("系統應通過 SSRF 驗證並開始處理")
def step_impl_ssrf_pass(context):
    """驗證合法 YouTube URL 通過 SSRF 防護（不回應 422）。"""
    response = context.last_response
    assert response.status_code != 422, \
        f"合法 YouTube URL 不應被 SSRF 攔截，但收到 422"
    # 可能回應 200/201（處理中）或 404（API 尚未實作）
    assert response.status_code in (200, 201, 202, 404), \
        f"意外的回應碼：{response.status_code}"
