"""Then 回應應包含各方案用戶數 — Readmodel Then"""

from behave import then


@then('回應應包含各方案用戶數：')
def step_impl(context):
    resp = context.last_response
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "distribution" in data, f"回應缺少 distribution 欄位：{list(data.keys())}"
    dist = data["distribution"]
    assert isinstance(dist, dict), f"distribution 應為 dict，實際 {type(dist)}"

    for row in context.table:
        plan = row["方案"]
        actual_count = dist.get(plan)
        assert actual_count is not None, \
            f"distribution 缺少方案 '{plan}'，實際：{dist}"
        assert isinstance(actual_count, int) and actual_count >= 0, \
            f"方案 '{plan}' 用戶數應為非負整數，實際 {actual_count}"
