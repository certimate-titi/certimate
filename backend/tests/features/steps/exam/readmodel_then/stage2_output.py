"""Then steps for Stage 2 output verification — ReadModel Then"""

from behave import then


@then('階段 2 輸出應包含 {num_q:d} 題原始考題')
def step_impl(context, num_q):
    stage2 = context.memo.get("stage2_result")
    assert stage2 is not None, "找不到階段 2 的輸出結果"

    questions = stage2.get("questions", [])
    assert len(questions) == num_q, \
        f"階段 2 應有 {num_q} 題，但得到 {len(questions)} 題"


@then('每題應包含：')
def step_impl(context):
    stage2 = context.memo.get("stage2_result")
    assert stage2 is not None, "找不到階段 2 的輸出結果"

    questions = stage2.get("questions", [])
    for i, q in enumerate(questions):
        for row in context.table:
            field = row["欄位"]
            assert field in q, \
                f"第 {i+1} 題應包含 '{field}'，但只有 {list(q.keys())}"


@then('難易度分布應符合 Easy:{easy_pct}% Medium:{medium_pct}% Hard:{hard_pct}%（容許 {tolerance} 題）')
def step_impl(context, easy_pct, medium_pct, hard_pct, tolerance):
    stage2 = context.memo.get("stage2_result")
    assert stage2 is not None, "找不到階段 2 的輸出結果"

    questions = stage2.get("questions", [])
    total = len(questions)
    tolerance_val = int(tolerance.replace("±", ""))

    easy_expected = round(total * int(easy_pct) / 100)
    medium_expected = round(total * int(medium_pct) / 100)
    hard_expected = round(total * int(hard_pct) / 100)

    from collections import Counter
    counts = Counter(q["difficulty"] for q in questions)

    assert abs(counts.get("easy", 0) - easy_expected) <= tolerance_val, \
        f"Easy 題數應約 {easy_expected}，但得到 {counts.get('easy', 0)}"
    assert abs(counts.get("medium", 0) - medium_expected) <= tolerance_val, \
        f"Medium 題數應約 {medium_expected}，但得到 {counts.get('medium', 0)}"
    assert abs(counts.get("hard", 0) - hard_expected) <= tolerance_val, \
        f"Hard 題數應約 {hard_expected}，但得到 {counts.get('hard', 0)}"
