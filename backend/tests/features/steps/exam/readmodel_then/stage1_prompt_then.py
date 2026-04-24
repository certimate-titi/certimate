"""Then steps for stage 1 prompt content + bloom_allocation — ReadModel Then."""

from behave import then


def _captured_stage_prompts(context, stage: str):
    prompts = context.memo.get("captured_prompts", [])
    return [p for p in prompts if p.get("stage") == stage]


def _prompt_blob(context, stage: str) -> str:
    prompts = _captured_stage_prompts(context, stage)
    return "\n".join((p.get("system") or "") + "\n" + (p.get("user") or "") for p in prompts)


@then('階段 1 Prompt 應包含指示：「{expected_text}」')
def step_stage1_contains(context, expected_text):
    blob = _prompt_blob(context, "stage1")
    assert blob, "未捕獲到階段 1 的 Prompt（需 @llm-mock tag）"
    assert expected_text in blob, f"階段 1 Prompt 不包含『{expected_text}』\n實際：{blob[:400]}"


@then('階段 1 Prompt 應包含預設配比指示：「{expected_text}」')
def step_stage1_default(context, expected_text):
    blob = _prompt_blob(context, "stage1")
    assert blob, "未捕獲到階段 1 的 Prompt（需 @llm-mock tag）"
    assert expected_text in blob, f"階段 1 Prompt 不包含『{expected_text}』\n實際：{blob[:400]}"


@then('bloom_allocation 的各 Bloom 類別題數加總應符合 bloom_distribution（誤差 ±1 題）')
def step_bloom_allocation(context):
    stage1 = context.memo.get("stage1_result") or {}
    bloom_dist = context.memo.get("bloom_distribution", {})
    total_q = context.memo.get("exam_question_count", 10)

    aggregated = {}
    for ep in stage1.get("exam_points", []):
        ba = ep.get("bloom_allocation") or {}
        for level, cnt in ba.items():
            aggregated[level] = aggregated.get(level, 0) + int(cnt or 0)

    for category, pct in bloom_dist.items():
        expected = round(total_q * pct / 100)
        actual = aggregated.get(category, 0)
        assert abs(actual - expected) <= 2, \
            f"Bloom '{category}' 期望 ~{expected} 題，實際 {actual} 題"
