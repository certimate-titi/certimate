"""Given 使用者已提交合法測驗設定並建立測驗任務 — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.repositories.exam_repository import ExamRepository


@given('使用者 "{email}" 已提交合法測驗設定並建立測驗任務 ID 為 {task_id:d}')
def step_impl(context, email, task_id):
    db = context.db_session
    repo = ExamRepository(db)

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    user_id = uuid.UUID(context.ids[email])

    # 取得預設科目
    subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    exam = Exam(
        id=uuid.UUID(int=task_id),
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.PENDING,
        total_questions=10,
    )
    repo.save(exam)
    context.ids[f"exam_{task_id}"] = str(exam.id)
    context.memo["current_exam_id"] = str(exam.id)
