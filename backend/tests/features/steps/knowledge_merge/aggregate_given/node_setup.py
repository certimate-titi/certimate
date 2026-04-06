"""Given 既有/新進節點設定 — Aggregate Given"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode


def _ensure_subject_id(context):
    """Ensure merge_subject_id is set from Background subjects."""
    if not hasattr(context, "memo"):
        context.memo = {}
    if "merge_subject_id" not in context.memo:
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                context.memo["merge_subject_id"] = val
                break


@given('既有節點 "{name}"（source_origin: {origin}, depth: {depth:d}）')
def step_existing_node_with_meta(context, name, origin, depth):
    db = context.db_session
    _ensure_subject_id(context)

    subject_id_str = context.memo.get("merge_subject_id")
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    if f"node_{name}" not in context.ids:
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=depth,
            sort_order=0,
            source_origin=origin,
        )
        db.add(node)
        db.flush()
        db.commit()
        context.ids[f"node_{name}"] = str(node.id)

    context.memo.setdefault("existing_node_names", []).append(name)
    context.memo[f"node_meta_{name}"] = {
        "source_origin": origin,
        "depth": depth,
    }


@given('新進節點 "{name}"（source_origin: {origin}, depth: {depth:d}）')
def step_incoming_node_with_meta(context, name, origin, depth):
    _ensure_subject_id(context)

    context.memo.setdefault("incoming_nodes", []).append({
        "name": name,
        "depth": depth,
        "parent_name": None,
        "source_origin": origin,
    })
    context.memo[f"incoming_{name}"] = {"name": name, "depth": depth, "source_origin": origin}


@given('既有主幹有 "{name}"（depth: {depth:d}, source_origin: {origin}）')
def step_existing_trunk_node(context, name, depth, origin):
    db = context.db_session
    _ensure_subject_id(context)

    subject_id_str = context.memo.get("merge_subject_id")
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    if f"node_{name}" not in context.ids:
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=depth,
            sort_order=0,
            source_origin=origin,
        )
        db.add(node)
        db.flush()
        db.commit()
        context.ids[f"node_{name}"] = str(node.id)

    context.memo.setdefault("existing_node_names", []).append(name)
    context.memo[f"node_meta_{name}"] = {
        "source_origin": origin,
        "depth": depth,
    }


@given('教材萃取出 "{name}"（depth: {depth:d}, source_origin: {origin}）')
def step_document_extracted_node(context, name, depth, origin):
    _ensure_subject_id(context)

    context.memo.setdefault("incoming_nodes", []).append({
        "name": name,
        "depth": depth,
        "parent_name": None,
        "source_origin": origin,
    })
    context.memo[f"incoming_{name}"] = {"name": name, "depth": depth, "source_origin": origin}


@given('AI 判斷 "{child}" 語意屬於 "{parent}" 的子概念')
def step_ai_semantic_parent(context, child, parent):
    if not hasattr(context, "memo"):
        context.memo = {}

    context.memo[f"ai_parent_{child}"] = parent
    # Update the incoming node's parent_name
    for node in context.memo.get("incoming_nodes", []):
        if node["name"] == child:
            node["parent_name"] = parent
            break
