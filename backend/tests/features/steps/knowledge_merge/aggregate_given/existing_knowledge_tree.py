"""Given 考科已有考古題逆向產出的知識樹 — Aggregate Given"""

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


@given('考科 "{subject_name}" 已有考古題逆向產出的知識樹：')
def step_impl(context, subject_name):
    db = context.db_session
    subject_id = uuid.UUID(context.ids[f"subject_name_{subject_name}"])

    if not hasattr(context, "memo"):
        context.memo = {}
    context.memo["merge_subject_id"] = str(subject_id)

    node_map = {}
    for row in context.table:
        name = row["節點名稱"]
        depth = int(row["層級"])
        source = row["來源"]

        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=depth,
            sort_order=len(node_map),
            source_origin=source,
        )
        db.add(node)
        db.flush()
        node_map[name] = node
        context.ids[f"node_{name}"] = str(node.id)

    db.commit()
    context.memo["existing_node_names"] = list(node_map.keys())


@given('既有知識樹有節點 "{name}"')
def step_existing_node(context, name):
    db = context.db_session
    _ensure_subject_id(context)

    subject_id_str = context.memo.get("merge_subject_id")
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    if f"node_{name}" not in context.ids:
        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=1,
            sort_order=0,
            source_origin="exam",
        )
        db.add(node)
        db.flush()
        db.commit()
        context.ids[f"node_{name}"] = str(node.id)

    context.memo.setdefault("existing_node_names", []).append(name)


@given('既有知識樹有 depth={d:d} 節點 "{name}" 和 depth={d2:d} 節點 "{name2}"')
def step_existing_nodes_with_depth(context, d, name, d2, name2):
    db = context.db_session
    _ensure_subject_id(context)

    subject_id_str = context.memo.get("merge_subject_id")
    subject_id = uuid.UUID(subject_id_str) if subject_id_str else None

    parent_node = None
    for node_name, depth in [(name, d), (name2, d2)]:
        if f"node_{node_name}" not in context.ids:
            node = KnowledgeNode(
                subject_id=subject_id,
                name=node_name,
                depth=depth,
                sort_order=0,
                source_origin="exam",
                parent_id=parent_node.id if parent_node and depth > 1 else None,
            )
            db.add(node)
            db.flush()
            context.ids[f"node_{node_name}"] = str(node.id)
            if parent_node is None:
                parent_node = node

    db.commit()
    context.memo.setdefault("existing_node_names", []).extend([name, name2])
