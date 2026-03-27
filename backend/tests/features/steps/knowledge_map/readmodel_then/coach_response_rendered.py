"""Then 左側主面板以氣泡對話框形式渲染出教練那充滿關懷與深度的專屬解析 — Read Model"""

from behave import then


@then('左側主面板以氣泡對話框形式渲染出教練那充滿關懷與深度的專屬解析')
def coach_response_rendered(context):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    # Check for AI coach reply content (either "reply" or "content" field)
    reply = data.get("reply") or data.get("content")
    assert reply, (
        f"回應應包含非空的 'reply' 或 'content' 欄位，實際欄位: {list(data.keys())}"
    )
    assert len(reply) > 0, "教練回覆內容不應為空"
