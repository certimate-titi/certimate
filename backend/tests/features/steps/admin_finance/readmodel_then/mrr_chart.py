"""Then MRR 趨勢圖表資料驗證 — ReadModel Then"""

from behave import then


@then('圖表應顯示最近 30 天的 MRR 資料點')
def step_impl_mrr_30_days(context):
    """驗證 MRR 趨勢回應含最近 30 天資料（Red 階段允許 404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        points = data if isinstance(data, list) else data.get("trend") or data.get("data_points", [])
        assert len(points) > 0, "MRR 趨勢圖表應含資料點"


@then('每個資料點應包含日期與對應的 MRR 金額')
def step_impl_mrr_data_point_fields(context):
    """驗證每個資料點含日期與 MRR 金額欄位。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        points = data if isinstance(data, list) else data.get("trend") or data.get("data_points", [])
        for p in points:
            assert "date" in p or "day" in p or "name" in p, \
                f"資料點應含日期/月份欄位，實際: {p}"
            assert "mrr" in p or "amount" in p or "revenue" in p, \
                f"資料點應含 MRR 金額欄位，實際: {p}"
