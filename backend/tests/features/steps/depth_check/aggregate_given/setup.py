"""Given setup — Feature 45 depth CHECK BDD."""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.merge_conflict import MergeConflict
from app.models.resource import Resource


@given('一筆 MergeConflict pending 等待 alice 決策')
def step_create_pending_conflict(context):
    """建一筆 pending MergeConflict 給 keep_separate 流程用。"""
    from tests.features.steps.scaffold_retrieval.aggregate_given.setup import (
        _ensure_user, _ensure_subject,
    )

    db = context.db_session
    user_id = _ensure_user(db, "alice@example.com")
    if not hasattr(context, "ids"):
        context.ids = {}
    context.ids["alice@example.com"] = str(user_id)
    subject_id = _ensure_subject(db)
    db.flush()

    # 建一筆 existing node 作為比對對象
    existing = KnowledgeNode(
        subject_id=subject_id,
        parent_id=None,
        name="既有概念 A",
        depth=1,
        sort_order=0,
    )
    db.add(existing)
    db.flush()

    conflict = MergeConflict(
        subject_id=subject_id,
        existing_node_id=existing.id,
        incoming_node_name="新概念 B（衝突）",
        similarity=0.85,
        status="pending_review",
        suggestion="keep_both",
    )
    db.add(conflict)
    db.commit()

    context.memo["conflict_id"] = str(conflict.id)
    context.memo["last_user_id"] = user_id
    context.memo["last_subject_id"] = subject_id
