"""Given 考科已有統一知識樹 — Aggregate Given"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode


@given('考科 "{subject_name}" 已有統一知識樹：')
def step_unified_tree(context, subject_name):
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

        # depth 1 nodes have no parent; depth 2 find parent from depth 1
        parent_id = None
        if depth == 2:
            # Find the last depth-1 node as parent
            for prev_name, prev_node in reversed(list(node_map.items())):
                if prev_node.depth == 1:
                    parent_id = prev_node.id
                    break

        node = KnowledgeNode(
            subject_id=subject_id,
            name=name,
            depth=depth,
            sort_order=len(node_map),
            source_origin=source,
            parent_id=parent_id,
        )
        db.add(node)
        db.flush()
        node_map[name] = node
        context.ids[f"node_{name}"] = str(node.id)

    db.commit()
    context.memo["unified_node_ids"] = [str(n.id) for n in node_map.values()]
