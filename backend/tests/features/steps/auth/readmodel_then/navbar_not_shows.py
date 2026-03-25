from behave import then


@then('前端導覽列不應顯示「{label}」連結')
def step_impl(context, label):
    response = context.last_response
    data = response.json()
    nav_items = data.get("nav_items") or data.get("navigation", [])

    found = any(
        item.get("label") == label
        for item in nav_items
    ) if isinstance(nav_items, list) else False

    assert not found, \
        f"導覽列不應包含 label='{label}' 的連結，但找到了: {nav_items}"
