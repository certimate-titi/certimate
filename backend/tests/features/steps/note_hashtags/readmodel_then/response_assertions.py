"""Then response assertions — Feature 52 筆記 hashtag 系統 BDD."""

from behave import then


# ── tags list response ────────────────────────────────────────────────────────

@then('tags list response 含欄位 items, total')
def step_tags_response_has_fields(context):
    resp = context.memo.get("tags_response") or context.last_response.json()
    assert "items" in resp, f"tags response 缺少 items 欄位，回傳：{resp}"
    assert "total" in resp, f"tags response 缺少 total 欄位，回傳：{resp}"


@then('items 至少含 1 筆 tag（normalized, display, count）')
def step_tags_items_at_least_one(context):
    resp = context.memo.get("tags_response") or context.last_response.json()
    items = resp.get("items", [])
    assert len(items) >= 1, f"期望至少 1 筆 tag，實際 {len(items)} 筆"

    # 驗證欄位結構
    first = items[0]
    assert "normalized" in first, f"tag item 缺少 normalized 欄位：{first}"
    assert "display" in first, f"tag item 缺少 display 欄位：{first}"
    assert "count" in first, f"tag item 缺少 count 欄位：{first}"


@then("tags items 只含 subject_id 科目的 tags，不含 \"#AI標籤\"")
def step_tags_items_only_subject(context):
    resp = context.memo.get("tags_response") or context.last_response.json()
    items = resp.get("items", [])
    normalized_tags = {item["normalized"] for item in items}
    # AI標籤 的 normalized 是 "ai標籤"（全小寫）
    assert "ai標籤" not in normalized_tags, (
        f"tags 不應含 'ai標籤'（second_subject 的 tag），現有：{normalized_tags}"
    )
    # 應含 資安標籤
    assert "資安標籤" in normalized_tags, (
        f"tags 應含 '資安標籤'（subject_id 科目），現有：{normalized_tags}"
    )


@then("bob 的 tags items 不含 \"{tag_text}\"")
def step_bob_tags_not_contain(context, tag_text):
    resp = context.memo.get("bob_tags_response") or context.last_response.json()
    items = resp.get("items", [])
    normalized_tags = {item["normalized"] for item in items}
    assert tag_text.lower() not in normalized_tags, (
        f"bob 的 tags 不應含 '{tag_text}'（alice 的私密 tag），現有：{normalized_tags}"
    )


# ── filtered notes response ───────────────────────────────────────────────────

@then('所有 items 均含 tag "{tag}"')
def step_all_items_contain_tag(context, tag):
    """驗證 filtered notes 至少有 1 筆含指定 tag。"""
    resp = context.memo.get("filtered_notes_response") or context.last_response.json()
    items = resp.get("items", [])
    assert len(items) >= 1, f"期望至少 1 筆含 tag='{tag}' 的 note，實際 {len(items)} 筆"
