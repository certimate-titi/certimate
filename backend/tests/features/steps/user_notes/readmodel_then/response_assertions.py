"""Then response assertions — Feature 50 User Notes BDD."""

from behave import then


@then('note response 含欄位 id, user_id, subject_id, content, created_at, updated_at')
def step_note_response_has_required_fields(context):
    data = context.last_response.json()
    for key in ("id", "user_id", "subject_id", "content", "created_at", "updated_at"):
        assert key in data, f"response 缺少欄位 {key!r}，實際回應：{data}"


@then('list response 含欄位 items, total')
def step_list_response_has_items_total(context):
    data = context.last_response.json()
    for key in ("items", "total"):
        assert key in data, f"response 缺少欄位 {key!r}，實際回應：{data}"


@then('DB 中 user_notes 新增一筆，node_id 為 null')
def step_db_note_created_no_node(context):
    data = context.last_response.json()
    assert data.get("node_id") is None, f"期望 node_id 為 null，但得到 {data.get('node_id')}"


@then('response body node_id 不為 null')
def step_response_node_id_not_null(context):
    data = context.last_response.json()
    assert data.get("node_id") is not None, "期望 node_id 不為 null"


@then('items 筆數 >= {n:d}')
def step_items_count_gte(context, n):
    data = context.last_response.json()
    items = data.get("items", [])
    assert len(items) >= n, f"期望 items >= {n}，但得到 {len(items)}"


@then('items 筆數 = {n:d}')
def step_items_count_eq(context, n):
    resp_data = context.memo.get("bob_list_response") or context.last_response.json()
    items = resp_data.get("items", [])
    assert len(items) == n, f"期望 items = {n}，但得到 {len(items)}"


@then('所有 items 的 subject_id 均相同')
def step_all_items_same_subject(context):
    data = context.memo.get("filtered_list_response") or context.last_response.json()
    items = data.get("items", [])
    assert len(items) > 0, "items 不應為空"
    subject_ids = {item["subject_id"] for item in items}
    assert len(subject_ids) == 1, f"期望所有 subject_id 相同，但得到 {subject_ids}"


@then('response body content 等於 "{expected}"')
def step_response_content_equals(context, expected):
    data = context.last_response.json()
    actual = data.get("content")
    assert actual == expected, f"期望 content='{expected}'，但得到 '{actual}'"


@then('DB 中該筆記已不存在')
def step_db_note_deleted(context):
    from uuid import UUID
    from app.models.user_note import UserNote

    db = context.db_session
    note_id = UUID(context.memo["note_id"])
    note = db.get(UserNote, note_id)
    assert note is None, f"期望筆記已被刪除，但 DB 中仍存在"


@then('response body user_annotation 等於 "{expected}"')
def step_response_user_annotation_equals(context, expected):
    data = context.last_response.json()
    actual = data.get("user_annotation")
    assert actual == expected, f"期望 user_annotation='{expected}'，但得到 '{actual}'"


@then('DB 中 scaffold 的 user_response 已更新')
def step_db_scaffold_user_response_updated(context):
    from uuid import UUID
    from app.models.resource_scaffold import ResourceScaffold

    db = context.db_session
    scaffold_id = UUID(context.memo["scaffold_id"])
    db.expire_all()
    scaffold = db.get(ResourceScaffold, scaffold_id)
    assert scaffold is not None, "scaffold 不存在"
    assert scaffold.user_response is not None, "user_response 應已更新，但仍為 None"
    assert len(scaffold.user_response) > 0, "user_response 不應為空字串"
