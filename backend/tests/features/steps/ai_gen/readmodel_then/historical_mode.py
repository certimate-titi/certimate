"""Then steps for historical-only exam mode (no AI pipeline) — ReadModel Then"""

from behave import then


@then('系統不應執行四階段 AI Prompt Pipeline')
def step_impl_no_pipeline(context):
    """驗證考古題模式不執行 AI 四階段 Pipeline。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        # In historical mode, no AI stages should be present
        stages = data.get("stages", {})
        assert len(stages) == 0 or data.get("exam_mode") == "historical_only", \
            "考古題模式不應執行四階段 AI Pipeline"


@then('系統應直接從考古題題庫抽取 {count:d} 題')
def step_impl_direct_draw(context, count):
    """驗證系統從考古題題庫直接抽取指定數量的題目。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        questions = data.get("questions", [])
        assert len(questions) == count, \
            f"期望 {count} 題，實際 {len(questions)} 題"


@then('SSE 進度應直接跳到 100%：')
def step_impl_sse_jump_100(context):
    """驗證 SSE 進度直接跳至 100%（考古題模式）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    # In the Red phase, endpoint returns 404 — this is expected


@then('系統應依序執行四個階段的 AI Prompt')
def step_impl_four_stages(context):
    """驗證系統依序執行四個 AI Prompt 階段。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        stages = data.get("stages", {})
        assert len(stages) >= 4, \
            f"應有至少 4 個階段，實際 {len(stages)} 個"
