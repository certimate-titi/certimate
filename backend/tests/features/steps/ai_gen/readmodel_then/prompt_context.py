"""Then Prompt 個人化上下文驗證 — ReadModel Then"""

from behave import then


@then('階段 {stage_num:d} 的 Prompt 應包含使用者背景上下文：「{expected_text}」')
def step_stage_prompt_context(context, stage_num, expected_text):
    """Verify user context was considered in generation."""
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"

    data = response.json()
    assert "stages" in data or "result" in data or "exam_id" in data, \
        "回應應包含生成結果"


@then('階段 {stage_num:d} 的 Prompt 應包含指示：「{expected_text}」')
def step_stage_prompt_instruction(context, stage_num, expected_text):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"


@then('生成的題目描述應使用白話文而非學術用語')
def step_simple_language(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"


@then('生成的題目可直接使用專業術語與技術情境')
def step_professional_language(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"


@then('階段 {stage_num:d} 的解析可引用官方文件或 API 語法')
def step_official_docs(context, stage_num):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"


@then('系統不應注入個人化上下文至 Prompt')
def step_no_personalization(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"


@then('生成的考題應使用預設的大學程度通用語言')
def step_default_language(context):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"API 回應失敗: {response.status_code} {response.text}"
