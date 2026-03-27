"""Given 系統中有以下測驗 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.repositories.exam_repository import ExamRepository


STATUS_MAP = {
    "READY": ExamStatus.READY,
    "IN_PROGRESS": ExamStatus.IN_PROGRESS,
    "SUBMITTED": ExamStatus.SUBMITTED,
    "PENDING": ExamStatus.PENDING,
}


@given('系統中有以下測驗：')
def step_impl(context):
    db = context.db_session
    repo = ExamRepository(db)

    # Need a default subject for FK
    if "default_subject" not in context.ids:
        from app.models.subject import SubjectCategory, Subject
        cat = SubjectCategory(name="default_cat")
        db.add(cat)
        db.flush()
        subj = Subject(name="default_subject", category_id=cat.id)
        db.add(subj)
        db.flush()
        context.ids["default_subject"] = str(subj.id)

    subject_id = uuid.UUID(context.ids["default_subject"])

    for row in context.table:
        exam_id_int = int(row["測驗 ID"])
        user_id_key = row["使用者 ID"].strip()
        status_raw = row["狀態"].strip()
        total_questions = int(row["總題數"])
        duration = int(row["考試時長（分鐘）"])

        # Look up user UUID from context.ids
        user_uuid = uuid.UUID(context.ids[user_id_key])

        exam = Exam(
            id=uuid.UUID(int=exam_id_int),
            user_id=user_uuid,
            subject_id=subject_id,
            status=STATUS_MAP.get(status_raw, ExamStatus.PENDING),
            total_questions=total_questions,
            duration_minutes=duration,
        )

        # If IN_PROGRESS, set started_at
        if status_raw == "IN_PROGRESS":
            exam.started_at = datetime.now(timezone.utc)

        # If SUBMITTED, set started_at and submitted_at
        if status_raw == "SUBMITTED":
            exam.started_at = datetime.now(timezone.utc)
            exam.submitted_at = datetime.now(timezone.utc)

        repo.save(exam)
        context.ids[f"exam_{exam_id_int}"] = str(exam.id)
