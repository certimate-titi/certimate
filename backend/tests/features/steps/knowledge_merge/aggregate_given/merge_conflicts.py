"""Given 合併衝突相關前置資料 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.merge_conflict import MergeConflict


@given('考科 "{subject_name}" 有 {count:d} 筆未解決的合併衝突')
def step_conflicts_count(context, subject_name, count):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.ids[f"subject_name_{subject_name}"]
    subject_id = uuid.UUID(subject_id_str)
    context.memo["merge_subject_id"] = subject_id_str

    # Create actual knowledge nodes and conflict records in DB
    for i in range(count):
        # Create existing node
        existing_node = KnowledgeNode(
            subject_id=subject_id,
            name=f"既有節點_{i+1}",
            depth=1,
            sort_order=i,
            source_origin="exam",
        )
        db.add(existing_node)
        db.flush()

        # Create conflict record
        conflict = MergeConflict(
            subject_id=subject_id,
            existing_node_id=existing_node.id,
            incoming_node_name=f"新進節點_{i+1}",
            similarity=Decimal("0.72"),
            status="pending_review",
            suggestion="merge_as_child",
        )
        db.add(conflict)
        db.flush()
        context.ids[f"conflict_{i+1}"] = str(conflict.id)

    db.commit()
    context.memo["conflict_count"] = count


@given('有一筆合併衝突：既有 "{existing}" vs 新進 "{incoming}"')
def step_single_conflict(context, existing, incoming):
    db = context.db_session
    if not hasattr(context, "memo"):
        context.memo = {}

    subject_id_str = context.memo.get("merge_subject_id")
    if not subject_id_str:
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                subject_id_str = val
                break
    assert subject_id_str, "找不到 subject_id"
    subject_id = uuid.UUID(subject_id_str)

    # Create existing node if not already present
    if f"node_{existing}" not in context.ids:
        existing_node = KnowledgeNode(
            subject_id=subject_id,
            name=existing,
            depth=2,
            sort_order=0,
            source_origin="exam",
        )
        db.add(existing_node)
        db.flush()
        context.ids[f"node_{existing}"] = str(existing_node.id)
    else:
        existing_node = db.query(KnowledgeNode).filter_by(
            id=uuid.UUID(context.ids[f"node_{existing}"])
        ).first()

    # Create actual conflict record in DB
    conflict = MergeConflict(
        subject_id=subject_id,
        existing_node_id=existing_node.id,
        incoming_node_name=incoming,
        similarity=Decimal("0.72"),
        status="pending_review",
        suggestion="merge_as_child",
    )
    db.add(conflict)
    db.flush()
    db.commit()

    context.ids["conflict_1"] = str(conflict.id)
    context.memo["conflict_existing"] = existing
    context.memo["conflict_incoming"] = incoming
