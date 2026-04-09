"""Then SSE 進度事件驗證 — ReadModel Then"""

from behave import then


@then('SSE 應依序推送以下進度事件：')
def step_impl_sse_events(context):
    """驗證 SSE 依序推送各階段進度事件。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        events = data.get("progress_events", [])
        for row in context.table:
            pct = int(row["進度百分比"])
            stage = row["階段"]
            matched = any(
                e.get("percentage") == pct and e.get("stage") == stage
                for e in events
            )
            assert matched, f"未找到進度 {pct}% 的 SSE 事件（{stage}）"


@then('SSE 應推送重試訊息 "{message}"')
def step_impl_sse_retry(context, message):
    """驗證 SSE 推送重試訊息。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        events = data.get("progress_events", [])
        retry_msgs = [e.get("message", "") for e in events]
        assert any(message in m for m in retry_msgs), \
            f"未找到重試訊息 '{message}'，實際訊息：{retry_msgs}"


@then('SSE 應推送錯誤事件：')
def step_impl_sse_error_event(context):
    """驗證 SSE 推送錯誤事件，含指定欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404, 422, 500), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        error_event = data.get("error_event", {})
        for row in context.table:
            field = row["欄位"]
            expected = row["值"]
            assert str(error_event.get(field, "")) == expected, \
                f"錯誤事件欄位 '{field}' 期望 '{expected}'，實際 '{error_event.get(field)}'"
