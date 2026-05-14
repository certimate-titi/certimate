"""When step actions — Feature 45 depth CHECK BDD."""

import uuid

from behave import when

from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource


@when('建立 KnowledgeNode(resource_id={res_label}, name="{name}", parent_id=NULL)（不指定 depth）')
def step_create_node_default_depth(context, res_label, name):
    """不傳 depth — 驗證 ORM default 值合規。"""
    db = context.db_session
    rid = context.memo.get("last_resource_id")
    if not rid:
        res = (
            context.memo.get("resources", {}).get(res_label)
            or context.memo.get("last_resource_obj")
        )
        rid = str(res.id) if res else None
    assert rid, f"找不到資源 {res_label}"

    node = KnowledgeNode(
        resource_id=uuid.UUID(rid),
        name=name,
        parent_id=None,
    )
    db.add(node)
    try:
        db.commit()
        db.refresh(node)
    except Exception as e:
        db.rollback()
        context.memo["last_node_error"] = str(e)
        context.memo["last_created_node"] = None
        return
    context.memo["last_created_node"] = node


@when('建立 KnowledgeNode(resource_id={res_label}, name="{name}", parent_id=NULL, depth={depth:d})')
def step_create_node_with_depth(context, res_label, name, depth):
    """指定 depth — 驗證 migration 100 解除上限後 depth>3 可寫入。"""
    db = context.db_session
    rid = context.memo.get("last_resource_id")
    if not rid:
        res = (
            context.memo.get("resources", {}).get(res_label)
            or context.memo.get("last_resource_obj")
        )
        rid = str(res.id) if res else None
    assert rid, f"找不到資源 {res_label}"

    node = KnowledgeNode(
        resource_id=uuid.UUID(rid),
        name=name,
        parent_id=None,
        depth=depth,
    )
    db.add(node)
    try:
        db.commit()
        db.refresh(node)
    except Exception as e:
        db.rollback()
        context.memo["last_node_error"] = str(e)
        context.memo["last_created_node"] = None
        return
    context.memo["last_created_node"] = node


@when('呼叫 KnowledgeMapService.build_for_resource("{res_label}")')
def step_call_knowledge_map_build(context, res_label):
    """直接走 _generate_knowledge_tree 路徑（簡化版 build_for_resource 內部）。"""
    from app.repositories.knowledge_node_repository import KnowledgeNodeRepository
    from app.repositories.resource_repository import ResourceRepository
    from app.services.knowledge_map_service import KnowledgeMapService

    db = context.db_session
    resources = context.memo.get("resources", {})
    res = resources.get(res_label) or context.memo.get("last_resource_obj")
    assert res is not None, (
        f"找不到資源 {res_label!r}；memo.resources keys={list(resources.keys())}, "
        f"last_resource_obj={context.memo.get('last_resource_obj')}"
    )

    svc = KnowledgeMapService(ResourceRepository(db), KnowledgeNodeRepository(db))
    try:
        svc._generate_knowledge_tree(res)
        db.commit()
    except Exception as e:
        db.rollback()
        context.memo["last_node_error"] = str(e)
        return

    # 取 root（parent_id=NULL）
    root = (
        db.query(KnowledgeNode)
        .filter_by(resource_id=res.id, parent_id=None)
        .first()
    )
    context.memo["last_created_node"] = root


@when('用戶 alice 對該衝突 POST decision={body}')
def step_resolve_conflict(context, body):
    """直接呼叫 KnowledgeMergeService.resolve_conflict（避走 HTTP auth）。"""
    import json
    from app.services.knowledge_merge_service import KnowledgeMergeService

    db = context.db_session
    action = json.loads(body).get("action")
    user_id = context.memo["last_user_id"]
    conflict_id = context.memo["conflict_id"]

    svc = KnowledgeMergeService(db)
    try:
        result = svc.resolve_conflict(str(user_id), conflict_id, action)
        db.commit()
    except Exception as e:
        db.rollback()
        context.memo["last_node_error"] = str(e)
        return

    context.memo["resolve_result"] = result
    # 撈剛建立的新節點（incoming_node_name + parent_id NULL）
    new_node = (
        db.query(KnowledgeNode)
        .filter_by(name="新概念 B（衝突）", parent_id=None)
        .order_by(KnowledgeNode.id.desc())
        .first()
    )
    context.memo["last_created_node"] = new_node
