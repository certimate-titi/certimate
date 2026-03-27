"""Then 面板的對話歷史紀錄中，會以 Markdown 格式高亮顯示當前節點萃取的原文與重點 — Read Model"""

from behave import then


@then('面板的對話歷史紀錄中，會以 Markdown 格式高亮顯示當前節點萃取的原文與重點')
def markdown_highlight(context):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "source_text" in data, (
        f"回應缺少 'source_text' 欄位，實際欄位: {list(data.keys())}"
    )
    assert data["source_text"], "source_text 不應為空"
