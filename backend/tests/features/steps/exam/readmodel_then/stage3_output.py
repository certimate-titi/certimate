"""Then steps for Stage 3 output verification — ReadModel Then"""

from collections import Counter

from behave import then


@then('階段 3 輸出中每題應包含：')
def step_impl(context):
    stage3 = context.memo.get("stage3_result")
    assert stage3 is not None, "找不到階段 3 的輸出結果"

    questions = stage3.get("questions", [])
    assert len(questions) > 0, "階段 3 應有考題輸出"

    for i, q in enumerate(questions):
        for row in context.table:
            field = row["欄位"]
            assert field in q, \
                f"第 {i+1} 題應包含 '{field}'，但只有 {list(q.keys())}"


@then('干擾項應具備「表面合理但本質錯誤」的特性')
def step_impl(context):
    stage3 = context.memo.get("stage3_result")
    assert stage3 is not None, "找不到階段 3 的輸出結果"

    questions = stage3.get("questions", [])
    for i, q in enumerate(questions):
        reasons = q.get("distractor_reasons", {})
        assert len(reasons) == 3, \
            f"第 {i+1} 題應有 3 個干擾項原因，但得到 {len(reasons)}"


@then('正確答案在四個選項中的位置應隨機分布')
def step_impl(context):
    stage3 = context.memo.get("stage3_result")
    assert stage3 is not None, "找不到階段 3 的輸出結果"

    questions = stage3.get("questions", [])
    positions = [q.get("correct_index", 0) for q in questions]

    # Verify there is some distribution (not all the same position)
    unique_positions = set(positions)
    # With 10 questions, expect at least 2 different positions
    assert len(unique_positions) >= 2, \
        f"正確答案位置應隨機分布，但所有答案都在位置 {positions}"
