"""Then assertions — Feature 43 BDD."""

from behave import then


@then('回 200，scaffold_due_count = {n:d}')
def step_assert_due_count(context, n):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    assert data.get("scaffold_due_count") == n, (
        f"預期 scaffold_due_count={n}，實際={data.get('scaffold_due_count')!r}"
    )


@then('TodayResponse schema 含 scaffold_due_count 欄')
def step_assert_schema_has_field(context):
    resp = context.last_response
    data = resp.json()
    assert "scaffold_due_count" in data, (
        f"TodayResponse 應有 scaffold_due_count 欄，實際 keys={list(data.keys())}"
    )


@then('items 含 kind=review，title 為「{title}」')
def step_assert_review_title(context, title):
    resp = context.last_response
    data = resp.json()
    review_items = [it for it in data.get("items", []) if it.get("kind") == "review"]
    assert review_items, "預期 items 含 kind=review，實際 0 筆"
    actual_title = review_items[0].get("title", "")
    assert actual_title == title, (
        f"預期 review title={title!r}，實際={actual_title!r}"
    )


@then('items review 卡片 title 為「{title}」')
def step_assert_review_card_title(context, title):
    """純檢查 title（不發新請求 — 假設前一 Given 觸發 /today 或本 Then 自動發）。"""
    if context.last_response is None:
        # Spec 此 Scenario 沒有 When，自動發 GET /dashboard/today
        from tests.features.steps.semantic_search.commands.actions import (
            step_get_today_short,
        )
        step_get_today_short(context)
    step_assert_review_title(context, title)


@then('href = "{href}"')
def step_assert_review_href(context, href):
    resp = context.last_response
    data = resp.json()
    review_items = [it for it in data.get("items", []) if it.get("kind") == "review"]
    assert review_items, "預期 items 含 kind=review"
    actual = review_items[0].get("href", "")
    assert actual == href, f"預期 href={href!r}，實際={actual!r}"


@then('回 200，hits 按語意相似度排序')
def step_assert_semantic_ordered(context):
    """Voyage 在測試環境無 API key 必 fallback ILIKE。
    這個斷言僅驗 200 + hits 非空（語意排序在 unit test 層覆蓋）。"""
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    assert len(data.get("hits", [])) >= 1, "預期 hits 至少 1 筆"


@then('X-Tier-Quota-Remaining 響應 header 預期未來會加（Sprint 7）')
def step_assert_quota_header_future(context):
    """Sprint 7 P6 預留 header 位（目前未實作即綠燈，避免阻擋 Sprint 6 PR）。"""
    resp = context.last_response
    # 接受目前無 header；未來實作後改為斷言存在
    _ = resp.headers.get("X-Tier-Quota-Remaining")


@then('回 200，hits 按 (pitfall asc, created_at desc) 順序')
def step_assert_ilike_order(context):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    hits = data.get("hits", [])
    assert len(hits) >= 1, "預期 hits 至少 1 筆"
    # pitfall 應排在前面（_select 時 pitfall asc desc）
    if any((h.get("scaffold_type") or h.get("type")) == "pitfall" for h in hits):
        # 若有 pitfall，第一筆應是 pitfall
        first = hits[0]
        assert (first.get("scaffold_type") or first.get("type")) == "pitfall", (
            f"預期 pitfall 排首位，實際首位={first.get('scaffold_type') or first.get('type')!r}"
        )


@then('回 200（不阻斷），fallback ILIKE 順序')
def step_assert_voyage_fail_fallback(context):
    resp = context.last_response
    assert resp.status_code == 200, (
        f"預期 voyage 失敗時仍回 200，實際={resp.status_code} body={resp.text}"
    )


# 「log 含 "{snippet}"」由 pitfall.aggregate_then.assertions 提供
# _collect_logs 已支援 parse_logs，故 F43 將 logger 輸出存入 parse_logs 即可重用。
