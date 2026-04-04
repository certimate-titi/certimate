"""Given 該題修正後已連續 N 次「確定+答對」— Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus


@given('該題修正後已連續 {count:d} 次「確定+答對」')
def step_impl(context, count):
    db = context.db_session
    question_id = uuid.UUID(context.memo["current_question_id"])
    user_id = uuid.UUID(context.memo["current_user_id"])
    now = datetime.now(timezone.utc)

    # 取得 subject_id
    subject_id = uuid.UUID(context.memo["ai_subject_id"])

    # 建立 N 筆 confidence=high, is_correct=true 的答案
    for i in range(count):
        exam = Exam(
            user_id=user_id,
            subject_id=subject_id,
            status=ExamStatus.SUBMITTED,
            total_questions=1,
        )
        db.add(exam)
        db.flush()

        answer = Answer(
            exam_id=exam.id,
            question_id=question_id,
            user_id=user_id,
            selected_answer="A",
            is_correct=True,
            confidence="high",
            answered_at=now - timedelta(days=30 - i),
        )
        db.add(answer)

    db.commit()
    context.memo["blind_spot_correction_count"] = count


@given('最後一次答對日為 {days:d} 天前')
def step_last_correct(context, days):
    db = context.db_session
    question_id = uuid.UUID(context.memo["current_question_id"])

    # 更新最後一筆答案的 answered_at
    last_answer = db.query(Answer).filter_by(
        question_id=question_id, is_correct=True
    ).order_by(Answer.answered_at.desc()).first()

    if last_answer:
        last_answer.answered_at = datetime.now(timezone.utc) - timedelta(days=days)
        db.commit()


@given('該題尚未連續 {count:d} 次「確定+答對」')
def step_not_corrected(context, count):
    # 不建立足夠的正確答案，只建立 1 筆（不足 count 筆）
    db = context.db_session
    question_id = uuid.UUID(context.memo["current_question_id"])
    user_id = uuid.UUID(context.memo["current_user_id"])
    subject_id = uuid.UUID(context.memo["ai_subject_id"])
    now = datetime.now(timezone.utc)

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=1,
    )
    db.add(exam)
    db.flush()

    answer = Answer(
        exam_id=exam.id,
        question_id=question_id,
        user_id=user_id,
        selected_answer="A",
        is_correct=True,
        confidence="high",
        answered_at=now - timedelta(days=1),
    )
    db.add(answer)
    db.commit()
