"""Then depth=1 節點數量 / 子節點限制 — Aggregate Then.

Feature 29 §「六大主題上限」契約驗證。
"""

import uuid

from behave import then

from app.models.knowledge_node import KnowledgeNode


@then('統一知識樹的 depth=1 節點數量應 <= {limit:d}')
def step_depth1_count_le(context, limit):
    db = context.db_session
    subject_id_str = context.memo.get("merge_subject_id")
    assert subject_id_str, "找不到 merge_subject_id"
    subject_id = uuid.UUID(subject_id_str)

    count = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id, KnowledgeNode.depth == 1)
        .count()
    )
    assert count <= limit, (
        f"統一知識樹 depth=1 節點數量為 {count}，超過上限 {limit}"
    )
    context.memo["actual_depth1_count"] = count


@then('合併後 depth=1 節點數量應 <= {limit:d}')
def step_merged_depth1_count_le(context, limit):
    """合併對齊後的 depth=1 上限驗證（同上邏輯，獨立步驟句型）。"""
    db = context.db_session
    subject_id_str = context.memo.get("merge_subject_id")
    assert subject_id_str, "找不到 merge_subject_id"
    subject_id = uuid.UUID(subject_id_str)

    count = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id, KnowledgeNode.depth == 1)
        .count()
    )
    assert count <= limit, (
        f"合併後 depth=1 節點數量為 {count}，超過上限 {limit}"
    )
    context.memo["actual_depth1_count"] = count


@then('每個 depth=1 節點下應有至少 {min_children:d} 個 depth=2 子節點')
def step_each_depth1_has_min_children(context, min_children):
    db = context.db_session
    subject_id_str = context.memo.get("merge_subject_id")
    assert subject_id_str, "找不到 merge_subject_id"
    subject_id = uuid.UUID(subject_id_str)

    depth1_nodes = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id, KnowledgeNode.depth == 1)
        .all()
    )
    assert depth1_nodes, "找不到任何 depth=1 節點"

    for d1 in depth1_nodes:
        child_count = (
            db.query(KnowledgeNode)
            .filter(
                KnowledgeNode.parent_id == d1.id,
                KnowledgeNode.depth == 2,
            )
            .count()
        )
        assert child_count >= min_children, (
            f"depth=1 節點 '{d1.name}' 只有 {child_count} 個 depth=2 子節點，"
            f"應至少 {min_children} 個"
        )


@then('新面向應被合併到既有核心主題下，或作為 depth=2 子節點新增')
def step_new_facets_merged_or_demoted(context):
    """驗證合併規則：新面向要嘛升為新 depth=1（前提是 depth=1 仍 ≤ 6），
    要嘛被降級為 depth=2 子節點（合併到既有核心主題下）。
    """
    new_facet_count = context.memo.get("new_facet_count")
    assert new_facet_count is not None, (
        "memo 缺 new_facet_count（請確認 Given 「又上傳了 N 份新教材」執行過）"
    )

    promoted = context.memo.get("new_facets_promoted", 0)
    merged = context.memo.get("new_facets_merged_as_children", 0)

    # 所有新面向必須有處置
    assert promoted + merged == new_facet_count, (
        f"新面向處置不完整：新增 {promoted} + 合併為子節點 {merged} "
        f"!= 總新面向 {new_facet_count}"
    )

    # 上限保護：合併後 depth=1 仍 ≤ 6
    db = context.db_session
    subject_id = uuid.UUID(context.memo["merge_subject_id"])
    depth1_count = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id, KnowledgeNode.depth == 1)
        .count()
    )
    assert depth1_count <= 6, (
        f"合併後 depth=1 節點 {depth1_count} 個，超過 6 個上限"
    )
