"""Given 存在科目 "{subject_alias}" 名稱 "{name}"，含 N 個 knowledge_node、M 個 exam"""

import uuid

from behave import given

from app.models.subject import Subject, SubjectCategory
from app.models.knowledge_node import KnowledgeNode
from app.models.exam import Exam, ExamStatus


def _ensure_category(db) -> uuid.UUID:
    cat = db.query(SubjectCategory).first()
    if cat is not None:
        return cat.id
    cat_id = uuid.uuid4()
    db.add(SubjectCategory(id=cat_id, name="預設分類"))
    db.flush()
    return cat_id


@given('存在科目 "{subject_alias}" 名稱 "{name}"，含 {node_count:d} 個 knowledge_node、{exam_count:d} 個 exam')
def step_impl(context, subject_alias, name, node_count, exam_count):
    db = context.db_session

    cat_id = _ensure_category(db)
    subj_id = uuid.uuid4()
    subject = Subject(
        id=subj_id,
        category_id=cat_id,
        name=name,
        scope="platform",
    )
    db.add(subject)
    db.flush()

    # knowledge nodes
    for i in range(node_count):
        node = KnowledgeNode(
            id=uuid.uuid4(),
            subject_id=subj_id,
            parent_id=None,
            name=f"{name}-node-{i}",
            depth=0,
            sort_order=i,
        )
        db.add(node)

    # exams（need a user to own exam — pick first user in context.ids if available）
    user_id = None
    for k, v in context.ids.items():
        if "@" in k:
            user_id = uuid.UUID(v)
            break
    if exam_count > 0 and user_id is not None:
        for i in range(exam_count):
            exam = Exam(
                id=uuid.uuid4(),
                user_id=user_id,
                subject_id=subj_id,
                status=ExamStatus.PENDING.value,
                total_questions=10,
            )
            db.add(exam)

    db.commit()
    context.ids[subject_alias] = str(subj_id)
