"""Given 科目有 N 題考古題和 M 題 AI 生成題 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.repositories.subject_repository import SubjectRepository
from app.repositories.user_repository import UserRepository


@given('科目 "{subject_name}" 有 {hist:d} 題考古題和 {ai:d} 題 AI 生成題')
def step_impl(context, subject_name, hist, ai):
    db = context.db_session

    user_repo = UserRepository(db)
    user = user_repo.find_by_email("alice@example.com")
    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)

    now = datetime.now(timezone.utc)

    # 建立 Exam（用於掛題目）
    exam = Exam(
        user_id=user.id,
        subject_id=subject.id,
        status=ExamStatus.SUBMITTED,
        total_questions=hist + ai,
    )
    db.add(exam)
    db.flush()

    # 建立 historical 題目
    for i in range(hist):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"考古題 {i + 1}",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
            source_type="historical",
            historical_source="111年第1次",
        )
        db.add(q)

    # 建立 ai_generated 題目
    for i in range(ai):
        q = Question(
            exam_id=exam.id,
            question_number=hist + i + 1,
            content=f"AI 生成題 {i + 1}",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="A",
            source_type="ai_generated",
            quality_flag="ok",
            expires_at=now + timedelta(days=7),
        )
        db.add(q)

    db.commit()

    context.memo["count_exam_id"] = str(exam.id)
    context.memo["count_subject_name"] = subject_name
