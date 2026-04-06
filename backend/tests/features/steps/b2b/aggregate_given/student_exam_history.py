"""Given 學員已完成考試紀錄建立 — Aggregate Given"""

import uuid
from datetime import datetime

from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'學員 "(?P<email>[^"]+)" 已完成以下考試：')
def step_impl(context, email):
    """Create exam records in DB for the student."""
    from app.models.exam import Exam, ExamStatus
    from app.models.subject import Subject, SubjectCategory

    user_id = context.ids[email]

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

    exams_data = []
    for row in context.table:
        exam_int_id = int(row["考試 ID"])
        exam_uuid = uuid.UUID(int=exam_int_id)
        score = int(row["分數"])
        total = int(row["總題數"])
        correct = int(row["正確數"])
        submitted = row["繳交時間"]

        exam = Exam(
            id=exam_uuid,
            user_id=uuid.UUID(user_id) if isinstance(user_id, str) else user_id,
            subject_id=subject.id,
            status=ExamStatus.SUBMITTED.value,
            total_questions=total,
            score=score,
            correct_count=correct,
            submitted_at=datetime.fromisoformat(submitted),
        )
        context.db_session.add(exam)
        exams_data.append({
            "id": str(exam_uuid),
            "score": score,
            "total_questions": total,
            "correct_count": correct,
            "submitted_at": submitted,
        })
        # Store exam mapping
        context.ids[str(exam_int_id)] = str(exam_uuid)

    context.db_session.commit()
    context.memo.setdefault("student_exams", {})[email] = exams_data


use_step_matcher("parse")
