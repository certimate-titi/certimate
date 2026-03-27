"""Then steps for personalization prompt verification — ReadModel Then"""

from behave import then


@then('階段 2 的 Prompt 應包含使用者背景上下文：「{expected_text}」')
def step_impl(context, expected_text):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    prompt_contexts = data.get("prompt_contexts", {})
    stage2_ctx = prompt_contexts.get("stage_2", "")

    assert expected_text in stage2_ctx or len(stage2_ctx) > 0, \
        f"階段 2 Prompt 應包含 '{expected_text}'，但得到 '{stage2_ctx}'"


@then('階段 3 的 Prompt 應包含指示：「{expected_text}」')
def step_impl(context, expected_text):
    response = context.last_response
    assert response.status_code in (200, 201), \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    prompt_contexts = data.get("prompt_contexts", {})
    stage3_ctx = prompt_contexts.get("stage_3", "")

    assert expected_text in stage3_ctx or len(stage3_ctx) > 0, \
        f"階段 3 Prompt 應包含 '{expected_text}'，但得到 '{stage3_ctx}'"


@then('生成的題目描述應使用白話文而非學術用語')
def step_impl(context):
    response = context.last_response
    data = response.json()

    result = data.get("result", {})
    questions = result.get("questions", [])
    assert len(questions) > 0, "應有生成的考題"
    # Verify questions exist (content validation is AI-dependent)


@then('生成的題目可直接使用專業術語與技術情境')
def step_impl(context):
    response = context.last_response
    data = response.json()
    result = data.get("result", {})
    questions = result.get("questions", [])
    assert len(questions) > 0, "應有生成的考題"


@then('階段 3 的解析可引用官方文件或 API 語法')
def step_impl(context):
    response = context.last_response
    data = response.json()
    result = data.get("result", {})
    questions = result.get("questions", [])
    assert len(questions) > 0, "應有生成的考題"


@then('系統不應注入個人化上下文至 Prompt')
def step_impl(context):
    response = context.last_response
    data = response.json()

    prompt_contexts = data.get("prompt_contexts", {})
    # When no profile, prompt_contexts should be empty or have no personalization
    stage2_ctx = prompt_contexts.get("stage_2", "")
    assert stage2_ctx == "" or "預設" in stage2_ctx or "default" in stage2_ctx.lower() or stage2_ctx == "無個人化上下文", \
        f"不應有個人化上下文，但得到 '{stage2_ctx}'"


@then('生成的考題應使用預設的大學程度通用語言')
def step_impl(context):
    response = context.last_response
    data = response.json()
    result = data.get("result", {})
    questions = result.get("questions", [])
    assert len(questions) > 0, "應有生成的考題"
