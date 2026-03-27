"""Then steps for Stage 1 output verification — ReadModel Then"""

from behave import then


@then('階段 1 輸出應包含：')
def step_impl(context):
    stage1 = context.memo.get("stage1_result")
    assert stage1 is not None, "找不到階段 1 的輸出結果"

    for row in context.table:
        field = row["欄位"]
        assert field in stage1, \
            f"階段 1 輸出應包含 '{field}'，但只有 {list(stage1.keys())}"


@then('所有 point_ratio 加總應等於 100%')
def step_impl(context):
    stage1 = context.memo.get("stage1_result")
    assert stage1 is not None, "找不到階段 1 的輸出結果"

    point_ratio = stage1.get("point_ratio", {})
    total = sum(point_ratio.values())
    assert total == 100, \
        f"所有 point_ratio 加總應為 100，但得到 {total}"
