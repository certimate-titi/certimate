"""Then — 斷言 (mindmap upgrade)."""

import uuid

from behave import then

from app.models.knowledge_node import KnowledgeNode
from app.models.resource_chunk import ResourceChunk


@then('檢索結果不應包含 "{node_name}" 節點的 chunks')
def step_impl_not_contain_node(context, node_name):
    node_id = uuid.UUID(context.memo["nodes"][node_name])
    results = context.memo["search_results"]
    node_ids = {
        r["chunk"].node_id for r in results if r["chunk"].node_id is not None
    }
    assert node_id not in node_ids, (
        f"預期不包含 {node_name} 節點 ({node_id}) 但實際出現在結果中"
    )


@then('檢索結果應包含 "{node_name}" 節點的 chunks')
def step_impl_contain_node(context, node_name):
    node_id = uuid.UUID(context.memo["nodes"][node_name])
    results = context.memo["search_results"]
    node_ids = {
        r["chunk"].node_id for r in results if r["chunk"].node_id is not None
    }
    assert node_id in node_ids, (
        f"預期包含 {node_name} 節點 ({node_id}) 但實際結果為 {node_ids}"
    )


@then('檢索結果應包含所有 "{node_name}" 節點的 chunks')
def step_impl_contain_all_node_chunks(context, node_name):
    node_id = uuid.UUID(context.memo["nodes"][node_name])
    results = context.memo["search_results"]
    matching = [r for r in results if r["chunk"].node_id == node_id]
    assert len(matching) >= 1, (
        f"預期包含 {node_name} 所有 chunks 但只有 {len(matching)}"
    )


@then('該節點的 support_strength 應為 {expected:f}')
def step_impl_strength_eq(context, expected):
    # 先 flush 確認 default 已套用
    context.db_session.flush()

    node_id = uuid.UUID(
        context.memo.get("strength_node_id") or context.memo.get("single_node_id")
    )
    node = context.db_session.query(KnowledgeNode).filter_by(id=node_id).first()
    assert node is not None, f"node {node_id} not found"
    actual = float(node.support_strength or 0)
    # 允許極小浮點誤差
    assert abs(actual - expected) < 0.01, (
        f"support_strength 預期 {expected}, 實際 {actual}"
    )


@then('回應的 tier 應為 "{tier}"')
def step_impl_tier_eq(context, tier):
    result = context.memo["display_result"]
    assert result["tier"] == tier, (
        f"tier 預期 {tier}, 實際 {result['tier']}"
    )


@then('回應的 needs_supplement 應為 {expected}')
def step_impl_needs_supplement(context, expected):
    result = context.memo["display_result"]
    expected_bool = expected.lower() == "true"
    assert result["needs_supplement"] is expected_bool, (
        f"needs_supplement 預期 {expected_bool}, 實際 {result['needs_supplement']}"
    )


@then('該資源的 chunks is_deleted 欄位應為 true')
def step_impl_chunks_soft_deleted(context):
    resource_id = uuid.UUID(context.memo["soft_del_resource_id"])
    rows = (
        context.db_session.query(ResourceChunk)
        .filter(ResourceChunk.resource_id == resource_id)
        .all()
    )
    assert len(rows) > 0, "soft delete 後 chunks 應仍存在於 DB"
    for r in rows:
        assert r.is_deleted is True, (
            f"chunk {r.id} is_deleted 預期 True, 實際 {r.is_deleted}"
        )


@then('檢索結果不應再返回這些 chunks')
def step_impl_soft_deleted_not_in_search(context):
    from app.repositories.resource_chunk_repository import ResourceChunkRepository
    resource_id = uuid.UUID(context.memo["soft_del_resource_id"])
    repo = ResourceChunkRepository(context.db_session)
    results = repo.search_similar(
        [0.1] * 1024, [resource_id], top_k=100
    )
    assert len(results) == 0, (
        f"軟刪後檢索應回傳空結果，實際有 {len(results)} 筆"
    )


@then('該資源的 chunks 應從 resource_chunks 表中物理刪除')
def step_impl_chunks_hard_deleted(context):
    resource_id = uuid.UUID(context.memo["soft_del_resource_id"])
    count = (
        context.db_session.query(ResourceChunk)
        .filter(ResourceChunk.resource_id == resource_id)
        .count()
    )
    assert count == 0, f"hard delete 後應為 0 筆，實際 {count}"


@then('回應應為 None (prompt 太短不建立 cache)')
def step_impl_cache_result_none(context):
    assert context.memo["cache_result"] is None, (
        f"預期 None，實際 {context.memo['cache_result']}"
    )


@then('stats.misses 應為 {n:d}')
def step_impl_cache_misses(context, n):
    svc = context.memo["cache_svc"]
    stats = svc.get_stats()
    assert stats["misses"] == n, (
        f"misses 預期 {n}，實際 {stats['misses']}"
    )


@then('回應應為 false')
def step_impl_cache_enabled_false(context):
    assert context.memo["cache_enabled_result"] is False, (
        f"is_enabled 預期 False，實際 {context.memo['cache_enabled_result']}"
    )
