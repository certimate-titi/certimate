"""Then 回應應包含訂閱分布資料 — Readmodel Then"""

from behave import then


@then('回應應包含訂閱分布資料')
def step_impl(context):
    resp = context.last_response
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "distribution" in data, f"回應缺少 distribution 欄位：{data}"
    dist = data["distribution"]
    assert isinstance(dist, dict), f"distribution 應為 dict，實際 {type(dist)}"
