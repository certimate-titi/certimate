"""Given step: 使用者 "{email}" 最近三次測驗分數為："""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.subject import Subject, SubjectCategory


def _ensure_subject(db):
    """Ensure a default subject exists for exam creation."""
    sub = db.query(Subject).first()
    if not sub:
        cat = db.query(SubjectCategory).first()
        if not cat:
            cat = SubjectCategory(name="預設分類")
            db.add(cat)
            db.commit()
            db.refresh(cat)
        sub = Subject(name="預設科目", category_id=cat.id)
        db.add(sub)
        db.commit()
        db.refresh(sub)
    return sub


@given('使用者 "{email}" 最近三次測驗分數為：')
def step_impl(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    subject = _ensure_subject(db)
    base_time = datetime.now(timezone.utc) - timedelta(hours=10)

    for row in context.table:
        seq = int(row["次序"])
        score = int(row["分數"])
        exam = Exam(
            user_id=user_id,
            subject_id=subject.id,
            status=ExamStatus.SUBMITTED,
            total_questions=20,
            score=score,
            created_at=base_time + timedelta(hours=seq),
            submitted_at=base_time + timedelta(hours=seq),
        )
        db.add(exam)
    db.commit()
