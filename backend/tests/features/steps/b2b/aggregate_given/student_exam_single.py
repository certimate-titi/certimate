"""Given 學員已完成單一考試 — Aggregate Given"""

import uuid
from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'學員 "(?P<email>[^"]+)" 已完成考試 (?P<exam_id>\d+)（分數 (?P<score>\d+)，共 (?P<total>\d+) 題）')
def step_impl(context, email, exam_id, score, total):
    """Create a single completed exam record in DB."""
    from app.models.exam import Exam, ExamStatus
    from app.models.subject import Subject, SubjectCategory

    user_id = context.ids[email]
    exam_int_id = int(exam_id)
    exam_uuid = uuid.UUID(int=exam_int_id)

    # Ensure a subject exists
    subject = context.db_session.query(Subject).first()
    if not subject:
        cat = context.db_session.query(SubjectCategory).first()
        if not cat:
            cat = SubjectCategory(id=uuid.uuid4(), name="金融證照")
            context.db_session.add(cat)
            context.db_session.flush()
        subject = Subject(
            id=uuid.uuid4(),
            name="測試科目",
            category_id=cat.id,
        )
        context.db_session.add(subject)
        context.db_session.flush()

    exam = Exam(
        id=exam_uuid,
        user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED.value,
        total_questions=int(total),
        score=int(score),
        correct_count=int(score) * int(total) // 100,  # approximate
    )
    context.db_session.add(exam)
    context.db_session.commit()

    # Store exam mapping
    context.ids[str(exam_int_id)] = str(exam_uuid)
    context.memo.setdefault("student_exams", {}).setdefault(email, []).append({
        "id": str(exam_uuid),
        "score": int(score),
        "total_questions": int(total),
    })


use_step_matcher("parse")
