"""Given 使用者在節點有錯題 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.question import Question


@given('使用者 "{email}" 在節點 "{node_name}" 有 {count:d} 題錯題')
def step_impl(context, email, node_name, count):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=count + 3,
    )
    db.add(exam)
    db.flush()

    for i in range(count + 3):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"節點 {node_name} 題目 #{i + 1}",
            correct_answer="A",
            option_a="選項A", option_b="選項B", option_c="選項C", option_d="選項D",
            node_id=node_id,
            difficulty="medium",
            source_type="historical",
            historical_source="test_exam_2024",
        )
        db.add(q)
        db.flush()

        is_wrong = i < count
        answer = Answer(
            exam_id=exam.id,
            question_id=q.id,
            user_id=user_id,
            selected_answer="B" if is_wrong else "A",
            is_correct=not is_wrong,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(answer)

    db.commit()
