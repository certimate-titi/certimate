"""Then 左側 75% 面板頂部即時更新顯示來源頁碼或影片時間戳 — Read Model"""

from behave import then


@then('左側 75% 面板頂部即時更新顯示 "來源頁碼：第 12 頁" 或 "影片時間戳：00:08:32"')
def source_citation_displayed(context):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "source_citation" in data, (
        f"回應缺少 'source_citation' 欄位，實際欄位: {list(data.keys())}"
    )

    citation = data["source_citation"]
    has_page = citation.get("source_page_number") is not None
    has_timestamp = citation.get("source_timestamp_seconds") is not None
    assert has_page or has_timestamp, (
        "source_citation 應包含 source_page_number 或 source_timestamp_seconds"
    )
