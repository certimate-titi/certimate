"""Given 使用者有個人題庫題目 — EPIC-035 M3/M4."""

import uuid

from behave import given

from app.models.question import Question
from app.models.resource import Resource
from app.models.subject import Subject, SubjectCategory


def _ensure_subject(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).first()
    if cat is None:
        cat = SubjectCategory(name="IT")
        db.add(cat)
        db.flush()
    subj = db.query(Subject).filter_by(name="EPIC-035 Personal").first()
    if subj is None:
        subj = Subject(name="EPIC-035 Personal", category_id=cat.id)
        db.add(subj)
        db.flush()
    return subj.id


def _create_personal_question(db, user_id: str, **kwargs) -> Question:
    uid = uuid.UUID(user_id)
    subject_id = _ensure_subject(db)
    # Personal question needs a source_resource (per ck_questions_has_parent)
    res = Resource(
        user_id=uid,
        subject_id=subject_id,
        name="盲推論來源.pdf",
        type="pdf",
        status="COMPLETED",
        file_size_bytes=1024,
    )
    db.add(res)
    db.flush()
    q = Question(
        content="AI 推論題目內容",
        option_a="選項A", option_b="選項B", option_c="選項C", option_d="選項D",
        source_resource_id=res.id,
        owner_user_id=uid,
        source_type="user_upload",
        tenant_id=res.tenant_id,
        question_number=1,
        **kwargs,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@given('使用者 "{email}" 有一個 needs_answer 個人題庫題目，AI 推論答案為 "{ai_answer}"、信心度 {conf:g}')
def step_blind(context, email, ai_answer, conf):
    user_id = context.ids.get(email)
    q = _create_personal_question(
        context.db_session,
        user_id,
        correct_answer=ai_answer,
        answer_source="ai_inferred",
        confidence=conf,
        needs_answer=True,
        never_for_scoring=True,
        explanation="AI 推論理由：選項 B 最符合題意。",
    )
    context.memo["last_question_id"] = str(q.id)


@given('使用者 "{email}" 有一個 T1 個人題庫題目，正解為 "{answer}"、answer_source={source}')
def step_t1(context, email, answer, source):
    user_id = context.ids.get(email)
    q = _create_personal_question(
        context.db_session,
        user_id,
        correct_answer=answer,
        answer_source=source,
        confidence=0.95,
        needs_answer=False,
        never_for_scoring=False,
    )
    context.memo["last_question_id"] = str(q.id)
