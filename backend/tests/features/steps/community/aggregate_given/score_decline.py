"""Given step: 使用者 "{email}" 連續 {n} 次測驗成績下滑（{scores}）"""

import re
import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.subject import Subject, SubjectCategory


def _ensure_subject(db):
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


@given('使用者 "{email}" 連續 {n:d} 次測驗成績下滑（{scores}）')
def step_impl(context, email, n, scores):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    # Delete existing exams for this user to avoid stale data from Background
    db.query(Exam).filter_by(user_id=user_id).delete()
    db.commit()

    subject = _ensure_subject(db)

    # Parse scores like "75 → 68 → 55"
    score_list = [int(s.strip()) for s in re.split(r'[→\->]+', scores)]
    base_time = datetime.now(timezone.utc) - timedelta(hours=10)

    for i, score in enumerate(score_list):
        exam = Exam(
            user_id=user_id,
            subject_id=subject.id,
            status=ExamStatus.SUBMITTED,
            total_questions=20,
            score=score,
            created_at=base_time + timedelta(hours=i),
            submitted_at=base_time + timedelta(hours=i),
        )
        db.add(exam)
    db.commit()
