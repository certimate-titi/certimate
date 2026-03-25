from behave import then


@then('前端導覽列應顯示「{label}」連結，路徑為 "{path}"')
def step_impl(context, label, path):
    response = context.last_response
    data = response.json()
    nav_items = data.get("nav_items") or data.get("navigation", [])

    found = any(
        item.get("label") == label and item.get("path") == path
        for item in nav_items
    ) if isinstance(nav_items, list) else False

    assert found, \
        f"導覽列中找不到 label='{label}', path='{path}' 的連結: {nav_items}"
