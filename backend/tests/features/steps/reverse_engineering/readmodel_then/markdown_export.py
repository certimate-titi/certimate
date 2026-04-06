"""Then Markdown 匯出驗證 — ReadModel Then"""

from behave import then


@then('回應 content_type 應為 "{content_type}"')
def step_impl(context, content_type):
    response = context.last_response
    actual_ct = response.headers.get("content-type", "")
    assert content_type in actual_ct, \
        f"預期 content-type 包含 '{content_type}'，實際為 '{actual_ct}'"


@then('內容應為巢狀列表格式，例如：')
def step_impl_nested_list(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"

    content = response.text
    # Verify it contains Markdown heading syntax
    assert "#" in content, \
        f"預期 Markdown 內容包含標題符號 '#'，實際內容：{content[:200]}"

    # Verify hierarchical structure (at least h1 and h2)
    has_h1 = any(line.startswith("# ") for line in content.split("\n"))
    has_h2 = any(line.startswith("## ") for line in content.split("\n"))
    assert has_h1, "預期 Markdown 包含一級標題（# ）"
    assert has_h2, "預期 Markdown 包含二級標題（## ）"
