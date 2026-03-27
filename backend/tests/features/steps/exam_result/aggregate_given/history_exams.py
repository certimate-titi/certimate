"""Given 系統中有以下歷史測驗記錄 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.subject import SubjectCategory, Subject
from app.repositories.exam_repository import ExamRepository


STATUS_MAP = {
    "SUBMITTED": ExamStatus.SUBMITTED,
    "IN_PROGRESS": ExamStatus.IN_PROGRESS,
    "READY": ExamStatus.READY,
    "PENDING": ExamStatus.PENDING,
}


@given('系統中有以下歷史測驗記錄：')
def step_impl(context):
    db = context.db_session
    repo = ExamRepository(db)

    if "default_subject" not in context.ids:
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
        correct_count = int(row.get("答對數", "0"))
        score = int(row.get("得分", "0")) if row.get("得分") else None
        passing_score = int(row.get("合格分數", "0")) if row.get("合格分數") else None
        submitted_str = row.get("提交時間", "")

        user_uuid = uuid.UUID(context.ids[user_id_key])

        exam = Exam(
            id=uuid.UUID(int=exam_id_int),
            user_id=user_uuid,
            subject_id=subject_id,
            status=STATUS_MAP.get(status_raw, ExamStatus.PENDING),
            total_questions=total_questions,
            correct_count=correct_count,
            score=score,
            passing_score=passing_score,
            duration_minutes=60,
        )

        if submitted_str:
            exam.submitted_at = datetime.fromisoformat(submitted_str).replace(tzinfo=timezone.utc)
            exam.started_at = exam.submitted_at

        if status_raw == "IN_PROGRESS":
            exam.started_at = datetime.now(timezone.utc)

        repo.save(exam)
        context.ids[f"exam_{exam_id_int}"] = str(exam.id)
