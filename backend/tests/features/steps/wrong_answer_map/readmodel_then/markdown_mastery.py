"""Then 錯題地圖 Markdown 匯出驗證 — ReadModel Then"""

from behave import then


@then('內容應包含掌握度標記，例如：')
def step_impl(context):
    response = context.last_response
    content = response.text

    # Check that content has heading markers with emoji indicators
    assert "#" in content, "Markdown 應包含 heading 標記"
    # Check for percentage or emoji markers
    has_emoji = any(c in content for c in ["🔴", "🟡", "🟢", "⚪"])
    has_percent = "%" in content or "(" in content
    assert has_emoji or has_percent, \
        f"Markdown 應包含掌握度標記（emoji 或百分比）, 內容: {content[:200]}"
