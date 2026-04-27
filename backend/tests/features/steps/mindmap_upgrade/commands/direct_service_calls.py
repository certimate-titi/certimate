"""When — 直接呼叫 service / repository (非 HTTP) — mindmap upgrade."""

import uuid

from behave import when


@when('系統以使用者身份查詢與 "{topic}" 相關的 chunks')
def step_impl_search_with_user(context, topic):
    from app.repositories.resource_chunk_repository import ResourceChunkRepository

    user_id = uuid.UUID(context.memo["user_id"])
    resource_id = uuid.UUID(context.memo["resource_id"])

    repo = ResourceChunkRepository(context.db_session)
    # Dummy query embedding (we only care about filter, not ranking)
    query_embedding = [0.1] * 1024

    results = repo.search_similar(
        query_embedding,
        [resource_id],
        top_k=100,
        user_id=user_id,
        exclude_mastered=True,
    )
    context.memo["search_results"] = results


@when('系統呼叫 MindmapStrengthService.recompute_for_node("{node_name}")')
def step_impl_recompute_node(context, node_name):
    from app.services.mindmap_strength_service import MindmapStrengthService
    node_id = uuid.UUID(context.memo["strength_node_id"])
    svc = MindmapStrengthService(context.db_session)
    try:
        strength = svc.recompute_for_node(node_id)
        context.memo["computed_strength"] = strength
        context.last_error = None
    except Exception as exc:  # noqa: BLE001
        context.last_error = {"message": str(exc)}


@when('系統呼叫 MindmapStrengthService.recompute_for_subject')
def step_impl_recompute_subject(context):
    from app.services.mindmap_strength_service import MindmapStrengthService
    subject_id = uuid.UUID(context.memo["chapter_subject_id"])
    svc = MindmapStrengthService(context.db_session)
    svc.recompute_for_subject(subject_id)


@when('系統計算 strength_to_display({value:f})')
def step_impl_strength_display(context, value):
    from app.services.mindmap_strength_service import MindmapStrengthService
    context.memo["display_result"] = MindmapStrengthService.strength_to_display(value)


@when('系統呼叫 delete_by_resource_id 不帶 hard 參數')
def step_impl_soft_delete(context):
    from app.repositories.resource_chunk_repository import ResourceChunkRepository
    repo = ResourceChunkRepository(context.db_session)
    resource_id = uuid.UUID(context.memo["soft_del_resource_id"])
    count = repo.delete_by_resource_id(resource_id)
    context.memo["deleted_count"] = count
    context.db_session.commit()


@when('系統呼叫 delete_by_resource_id 並帶 hard=true')
def step_impl_hard_delete(context):
    from app.repositories.resource_chunk_repository import ResourceChunkRepository
    repo = ResourceChunkRepository(context.db_session)
    resource_id = uuid.UUID(context.memo["soft_del_resource_id"])
    count = repo.delete_by_resource_id(resource_id, hard=True)
    context.memo["deleted_count"] = count
    context.db_session.commit()


@when('系統以 {n:d} 字的 system_prompt 呼叫 get_or_create_cache')
def step_impl_cache_small(context, n):
    svc = context.memo["cache_svc"]
    result = svc.get_or_create_cache(
        model="gemini-2.5-flash",
        system_prompt="a" * n,
        display_name="bdd-test",
    )
    context.memo["cache_result"] = result


@when('系統呼叫 GeminiCacheService.is_enabled()')
def step_impl_cache_is_enabled(context):
    from app.services.gemini_cache_service import GeminiCacheService
    svc = GeminiCacheService()
    context.memo["cache_enabled_result"] = svc.is_enabled()
