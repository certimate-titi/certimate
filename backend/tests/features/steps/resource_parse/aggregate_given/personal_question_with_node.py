"""Given 個人題庫題目 + 掛到知識節點 — EPIC-035 M4 never_for_scoring 隔離測試。"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.models.resource import Resource
from app.models.subject import Subject, SubjectCategory


@given('使用者 "{email}" 有一個掛在知識節點上的 never_for_scoring 個人題庫題目，正解為 "{answer}"')
def step_impl(context, email, answer):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    cat = db.query(SubjectCategory).first() or SubjectCategory(name="IT")
    if cat.id is None:
        db.add(cat)
        db.flush()
    subj = db.query(Subject).filter_by(name="EPIC-035 M4").first()
    if subj is None:
        subj = Subject(name="EPIC-035 M4", category_id=cat.id)
        db.add(subj)
        db.flush()

    node = KnowledgeNode(
        subject_id=subj.id,
        name="M4 測試節點",
    )
    db.add(node)
    db.flush()

    res = Resource(
        user_id=user_id,
        subject_id=subj.id,
        name="M4.pdf",
        type="pdf",
        status="COMPLETED",
        file_size_bytes=1024,
    )
    db.add(res)
    db.flush()

    q = Question(
        content="M4 never_for_scoring 題目",
        option_a="選項A", option_b="選項B", option_c="選項C", option_d="選項D",
        correct_answer=answer,
        source_resource_id=res.id,
        owner_user_id=user_id,
        source_type="user_upload",
        answer_source="ai_inferred",
        confidence=0.8,
        never_for_scoring=True,
        tenant_id=res.tenant_id,
        question_number=1,
        node_id=node.id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    context.memo["last_question_id"] = str(q.id)
