"""Then steps for stage 1 prompt inspection (via LLM mock) — ReadModel Then."""

from behave import then


def _captured_stage_prompts(context, stage: str):
    prompts = context.memo.get("captured_prompts", [])
    return [p for p in prompts if p.get("stage") == stage]


@then('階段 1 Prompt 應包含指示：「{expected_text}」')
def step_stage1_contains(context, expected_text):
    prompts = _captured_stage_prompts(context, "stage1")
    assert prompts, "未捕獲到階段 1 的 Prompt"
    blob = "\n".join((p.get("system") or "") + "\n" + (p.get("user") or "") for p in prompts)
    assert expected_text in blob, f"階段 1 Prompt 不包含『{expected_text}』\n實際：{blob[:400]}"


@then('階段 1 Prompt 應包含預設配比指示：「{expected_text}」')
def step_stage1_default(context, expected_text):
    prompts = _captured_stage_prompts(context, "stage1")
    assert prompts, "未捕獲到階段 1 的 Prompt"
    blob = "\n".join((p.get("system") or "") + "\n" + (p.get("user") or "") for p in prompts)
    assert expected_text in blob, f"階段 1 Prompt 不包含『{expected_text}』\n實際：{blob[:400]}"
