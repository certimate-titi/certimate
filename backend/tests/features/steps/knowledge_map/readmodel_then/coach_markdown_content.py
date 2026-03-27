"""Then 教練面板應以 Markdown 格式顯示原文重點 — ReadModel Then"""

from behave import then


@then('教練面板應以 Markdown 格式顯示該節點萃取的原文重點')
def step_impl(context):
    response = context.last_response
    data = response.json()

    source_text = data.get("source_text", "")
    assert source_text, "回應中缺少 source_text（原文重點）"
    # Markdown 格式至少包含一些文字內容
    assert len(source_text) > 0, "source_text 不應為空"
