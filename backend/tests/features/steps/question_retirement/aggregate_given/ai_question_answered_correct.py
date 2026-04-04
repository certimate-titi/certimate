"""Given 使用者於 N 天前答對了一題 AI 題 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 於 {days:d} 天前答對了一題 AI 題')
def step_impl(context, email, days):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name("證券商業務員")
    answered_at = datetime.now(timezone.utc) - timedelta(days=days)

    # 建立 Exam
    exam = Exam(
        user_id=user_id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=1,
        created_at=answered_at,
    )
    db.add(exam)
    db.flush()

    # 建立 AI 題
    q = Question(
        exam_id=exam.id,
        question_number=1,
        content="AI 生成題目：答對測試",
        option_a="選項 A",
        option_b="選項 B",
        option_c="選項 C",
        option_d="選項 D",
        correct_answer="A",
        source_type="ai_generated",
        quality_flag="ok",
        expires_at=answered_at + timedelta(days=7),
    )
    db.add(q)
    db.flush()

    # 建立正確答案
    answer = Answer(
        exam_id=exam.id,
        question_id=q.id,
        user_id=user_id,
        selected_answer="A",
        is_correct=True,
        confidence="high",
        answered_at=answered_at,
    )
    db.add(answer)
    db.commit()

    context.memo["ai_question_ids"] = [str(q.id)]
    context.memo["ai_exam_id"] = str(exam.id)
    context.memo["ai_subject_id"] = str(subject.id)
    context.memo["current_question_id"] = str(q.id)
