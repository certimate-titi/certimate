"""Then chunk 映射驗證 — Aggregate Then"""

import uuid

from behave import then
from sqlalchemy import text


@then('該科目所有 resource_chunks 的 node_id 不應為空')
def step_all_chunks_have_node_id(context):
    db = context.db_session
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    result = db.execute(text('''
        SELECT COUNT(*) FROM resource_chunks rc
        JOIN resources r ON rc.resource_id = r.id
        WHERE r.subject_id = :sid AND rc.node_id IS NULL
    '''), {'sid': uuid.UUID(subject_id)}).scalar()

    assert result == 0, (
        f"仍有 {result} 個 resource_chunks 的 node_id 為空"
    )


@then('至少有 {n:d} 個統一節點被映射到 chunks')
def step_min_nodes_with_chunks(context, n):
    db = context.db_session
    subject_id = context.memo.get("merge_subject_id")
    assert subject_id, "找不到 merge_subject_id"

    result = db.execute(text('''
        SELECT COUNT(DISTINCT rc.node_id) FROM resource_chunks rc
        JOIN resources r ON rc.resource_id = r.id
        WHERE r.subject_id = :sid AND rc.node_id IS NOT NULL
    '''), {'sid': uuid.UUID(subject_id)}).scalar()

    assert result >= n, (
        f"預期至少 {n} 個節點有 chunks 映射，實際只有 {result} 個"
    )
