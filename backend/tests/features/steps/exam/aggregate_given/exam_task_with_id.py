"""Given 使用者已提交測驗設定並建立測驗任務 ID 為 — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.repositories.exam_repository import ExamRepository


@given('使用者 "{email}" 已提交測驗設定並建立測驗任務 ID 為 {task_id:d}')
def step_impl(context, email, task_id):
    db = context.db_session
    repo = ExamRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    user_id = uuid.UUID(context.ids[email])

    subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    # Collect node_ids from context
    node_ids = []
    for key, val in context.ids.items():
        if key.startswith("node_"):
            node_ids.append(val)

    exam = Exam(
        id=uuid.UUID(int=task_id),
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.PENDING,
        total_questions=10,
        difficulty_distribution={
            "easy": 30, "medium": 50, "hard": 20,
            "node_ids": node_ids,
        },
    )
    repo.save(exam)
    context.ids[f"exam_{task_id}"] = str(exam.id)
    context.memo["current_exam_id"] = str(exam.id)
    context.memo["current_user_email"] = email
