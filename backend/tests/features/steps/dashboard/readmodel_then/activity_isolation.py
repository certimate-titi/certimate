"""Then activityItems 不應洩漏他人 resource — Readmodel Then（dashboard ownership isolation）"""

from behave import then


@then('activityItems 中不應包含 "{memo_key}" 的 resource_id')
def step_impl(context, memo_key):
    data = context.last_response.json()
    forbidden_id = context.ids.get(memo_key)
    assert forbidden_id is not None, f"memo_key '{memo_key}' 不在 context.ids 中"

    activity_items = data.get("activityItems", [])
    leaked = []
    for item in activity_items:
        # activity item 的 id 格式為 "act_res_<uuid>" — 檢查是否包含 forbidden_id
        item_id = str(item.get("id", ""))
        item_link = str(item.get("link", ""))
        if forbidden_id in item_id or forbidden_id in item_link:
            leaked.append(item)
    assert not leaked, (
        f"activityItems 洩漏了他人 resource '{memo_key}' ({forbidden_id})；"
        f"洩漏項目：{leaked}"
    )
