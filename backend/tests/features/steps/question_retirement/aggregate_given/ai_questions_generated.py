"""Given 使用者於 N 天前生成了 AI 題 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.repositories.subject_repository import SubjectRepository


@given('使用者 "{email}" 於 {days:d} 天前生成了 {count:d} 題 AI 題')
def step_impl(context, email, days, count):
    user_id = uuid.UUID(context.ids[email])
    db = context.db_session

    # 取得科目（使用 context.memo 中的或第一個可用科目）
    subject_name = context.memo.get("ai_gen_subject_name", "證券商業務員")
    subject_repo = SubjectRepository(db)
    subject = subject_repo.find_by_name(subject_name)
    subject_id = subject.id

    created_time = datetime.now(timezone.utc) - timedelta(days=days)

    # 建立 Exam
    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=count,
        created_at=created_time,
    )
    db.add(exam)
    db.flush()

    # 建立 AI 題目
    question_ids = []
    for i in range(count):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"AI 生成題目 {i + 1}",
            option_a="選項 A",
            option_b="選項 B",
            option_c="選項 C",
            option_d="選項 D",
            correct_answer="A",
            source_type="ai_generated",
            quality_flag="ok",
            expires_at=created_time + timedelta(days=7),
        )
        db.add(q)
        db.flush()
        question_ids.append(str(q.id))

    db.commit()
    context.memo["ai_question_ids"] = question_ids
    context.memo["ai_exam_id"] = str(exam.id)
    context.memo["ai_subject_id"] = str(subject_id)
