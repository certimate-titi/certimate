"""Internal API & render_prompt verification steps."""

from behave import given, when, then


# ── render_prompt 變數替換 ──────────────────────────────────────────────

@given('一段 prompt 模板內容為 "{template_text}"')
def step_impl(context, template_text):
    context.memo["render_template"] = template_text


@when('使用變數 {var_pairs} 進行替換')
def step_impl(context, var_pairs):
    from app.services.prompt_template_service import PromptTemplateService

    # Parse "subject_name="AWS SAA"、user_input="什麼是 EC2？""
    import re
    pairs = re.findall(r'(\w+)="([^"]*)"', var_pairs)
    variables = {k: v for k, v in pairs}

    template_text = context.memo["render_template"]
    result = PromptTemplateService.render_prompt(template_text, variables)
    context.memo["render_result"] = result


@then('替換結果應為 "{expected}"')
def step_impl(context, expected):
    actual = context.memo["render_result"]
    assert actual == expected, \
        f"替換結果不符，預期：{expected}，實際：{actual}"


@then('替換結果不應包含 "{placeholder}"')
def step_impl(context, placeholder):
    actual = context.memo["render_result"]
    assert placeholder not in actual, \
        f"替換結果仍包含 '{placeholder}'，實際：{actual}"


# ── Fallback 驗證 ──────────────────────────────────────────────────────

@when('以 service 查詢模板 "{name}"')
def step_impl(context, name):
    from app.services.prompt_template_service import PromptTemplateService

    svc = PromptTemplateService(context.db_session)
    result = svc.get_prompt_for_ai(name)
    context.memo["service_result"] = result


@then("service 應回傳 error 且 status_code 為 {code:d}")
def step_impl(context, code):
    result = context.memo["service_result"]
    assert result.get("error") is True, \
        f"預期 error=True，實際：{result}"
    assert result.get("status_code") == code, \
        f"預期 status_code={code}，實際：{result.get('status_code')}"
