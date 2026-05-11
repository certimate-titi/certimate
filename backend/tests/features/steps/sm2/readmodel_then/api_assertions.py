"""API 回應斷言 — Feature 42 /scaffold-reviews/due / /today / /concept-center."""

from behave import then


@then('回 200，total={total:d}，items 按 next_review_at 升序')
def step_assert_due_200_sorted(context, total):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    assert data["total"] == total, f"預期 total={total}，實際 {data['total']}"
    items = data["items"]
    timestamps = [it["next_review_at"] for it in items]
    sorted_ts = sorted(timestamps)
    assert timestamps == sorted_ts, (
        f"items 未按 next_review_at 升序：{timestamps}"
    )


@then('items.length ≤ {n:d}')
def step_assert_items_length_le(context, n):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code}"
    data = resp.json()
    assert len(data["items"]) <= n, (
        f"預期 items.length<={n}，實際 {len(data['items'])}"
    )


@then('resume.resource_id = {res_name}')
def step_assert_today_resume(context, res_name):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    expected = context.memo.get("expected_resource_id")
    assert data.get("resume") is not None, "預期 resume 非 null"
    assert data["resume"]["resource_id"] == expected, (
        f"預期 resume.resource_id={expected} ({res_name})，"
        f"實際={data['resume']['resource_id']}"
    )


@then('items 含 kind="{kind}" + kind="{kind2}"')
def step_assert_items_kinds_pair(context, kind, kind2):
    resp = context.last_response
    data = resp.json()
    kinds = {it["kind"] for it in data.get("items", [])}
    for k in (kind, kind2):
        assert k in kinds, f"預期 items 含 kind={k!r}，實際 kinds={kinds}"


@then('若 review_count > 0 也含 kind="{kind}"')
def step_assert_items_kind_review_conditional(context, kind):
    resp = context.last_response
    data = resp.json()
    if data.get("review_count", 0) > 0:
        kinds = {it["kind"] for it in data.get("items", [])}
        assert kind in kinds, (
            f"review_count={data['review_count']} > 0 但 items 不含 kind={kind!r}"
        )


@then('resume = null')
def step_assert_today_resume_null(context):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    assert data.get("resume") is None, f"預期 resume=null，實際={data.get('resume')!r}"


@then('items 不含 kind="{kind}"')
def step_assert_items_not_contains_kind(context, kind):
    resp = context.last_response
    data = resp.json()
    kinds = {it["kind"] for it in data.get("items", [])}
    assert kind not in kinds, f"預期 items 不含 kind={kind!r}，實際 kinds={kinds}"


@then('items 含 kind="{kind}"')
def step_assert_items_contains_kind(context, kind):
    resp = context.last_response
    data = resp.json()
    kinds = {it["kind"] for it in data.get("items", [])}
    assert kind in kinds, f"預期 items 含 kind={kind!r}，實際 kinds={kinds}"


@then('回 200，hits 含對應 scaffold')
def step_assert_concept_200_hit(context):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    hits = data.get("hits", [])
    assert len(hits) >= 1, f"預期 hits 至少 1 筆，實際 0 筆"
    keyword = context.memo.get("concept_keyword", "")
    if keyword:
        found = any(
            keyword in (h.get("content") or "") + (h.get("chapter_heading") or "")
            for h in hits
        )
        assert found, f"預期 hits 含關鍵字 {keyword!r}，實際 hits={hits[:2]}"


@then('回 422 含「{snippet}」')
def step_assert_concept_422(context, snippet):
    resp = context.last_response
    assert resp.status_code == 422, f"預期 422，實際 {resp.status_code} body={resp.text}"
    body = resp.text
    assert snippet in body, f"預期 422 body 含 {snippet!r}，實際:\n{body}"


@then('hits[0].scaffold_type = "{stype}"')
def step_assert_first_hit_type(context, stype):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text}"
    data = resp.json()
    hits = data.get("hits", [])
    assert len(hits) >= 1, "hits 為空"
    first = hits[0]
    actual_type = first.get("scaffold_type") or first.get("type")
    assert actual_type == stype, (
        f"預期 hits[0].scaffold_type={stype!r}，實際={actual_type!r}"
    )
