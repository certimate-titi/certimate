"""Given AI 題被軟刪除 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.repositories.subject_repository import SubjectRepository
from app.repositories.user_repository import UserRepository


def _create_soft_deleted_question(context, days):
    db = context.db_session
    now = datetime.now(timezone.utc)
    retired_at = now - timedelta(days=days)

    user_repo = UserRepository(db)
    user = user_repo.find_by_email("alice@example.com")
    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")

    exam = Exam(
        user_id=user.id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=1,
    )
    db.add(exam)
    db.flush()

    q = Question(
        exam_id=exam.id,
        question_number=1,
        content="AI 生成題目：軟刪除測試",
        option_a="選項 A",
        option_b="選項 B",
        option_c="選項 C",
        option_d="選項 D",
        correct_answer="A",
        source_type="ai_generated",
        quality_flag="ok",
        retired_at=retired_at,
        retention_reason="測試軟刪除",
    )
    db.add(q)
    db.flush()

    db.commit()
    context.memo["ai_question_ids"] = [str(q.id)]
    context.memo["current_question_id"] = str(q.id)
    context.memo["ai_exam_id"] = str(exam.id)
    context.memo["ai_subject_id"] = str(subject.id)


@given('一題 AI 題於 {days:d} 天前被軟刪除（retired_at 已設定）')
def step_impl(context, days):
    _create_soft_deleted_question(context, days)


@given('一題 AI 題於 {days:d} 天前被軟刪除')
def step_soft_deleted(context, days):
    _create_soft_deleted_question(context, days)
