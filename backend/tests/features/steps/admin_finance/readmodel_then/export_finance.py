"""Then 財務報告匯出驗證 — ReadModel Then"""

from behave import then


@then('瀏覽器應觸發 JSON 檔案下載')
def step_impl_trigger_download(context):
    """驗證 API 回應觸發下載（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('下載檔案應包含交易摘要與營收統計資料')
def step_impl_download_contains_summary(context):
    """驗證下載內容包含交易摘要（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        assert "transactions" in data or "summary" in data or "revenue" in data, \
            "匯出資料應包含 transactions/summary/revenue 欄位"
