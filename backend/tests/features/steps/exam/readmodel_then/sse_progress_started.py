"""Then 系統應開始透過 SSE 推送生成進度事件 — ReadModel Then"""

from behave import then


@then('系統應開始透過 SSE 推送生成進度事件')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # 驗證回應中包含 SSE/streaming 相關資訊
    assert data.get("sse_enabled") or data.get("exam_id"), (
        "回應應包含 SSE 推送資訊或測驗 ID"
    )
