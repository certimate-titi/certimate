"""Then 回應應包含最近 30 天的 MRR 趨勢資料點 — Readmodel Then"""

from behave import then


@then('回應應包含最近 30 天的 MRR 趨勢資料點')
def step_impl(context):
    resp = context.last_response
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "mrr_trend" in data, f"回應缺少 mrr_trend 欄位：{list(data.keys())}"
    mrr_trend = data["mrr_trend"]
    assert isinstance(mrr_trend, list), f"mrr_trend 應為 list，實際 {type(mrr_trend)}"
    assert len(mrr_trend) > 0, "mrr_trend 不應為空"
    # Each data point should have date and mrr
    for point in mrr_trend:
        assert "date" in point, f"MRR 資料點缺少 date 欄位：{point}"
        assert "mrr" in point, f"MRR 資料點缺少 mrr 欄位：{point}"
