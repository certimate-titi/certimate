"""Given 使用者在節點的作答紀錄 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.node_mastery import NodeMastery
from app.models.question import Question


@given('使用者 "{email}" 在節點 "{node_name}" 的作答紀錄為：')
def step_impl(context, email, node_name):
    db = context.db_session

    user_id = uuid.UUID(context.ids[email])
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    row = context.table[0]
    correct = int(row["答對數"])
    total = int(row["總作答數"])

    # Create exam + questions + answers
    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    exam = Exam(
        user_id=user_id,
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=total,
    )
    db.add(exam)
    db.flush()

    for i in range(total):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"作答紀錄題目 {node_name} #{i + 1}",
            correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=node_id,
            source_type="historical",
        )
        db.add(q)
        db.flush()

        is_correct = i < correct
        answer = Answer(
            exam_id=exam.id,
            question_id=q.id,
            user_id=user_id,
            selected_answer="A" if is_correct else "B",
            is_correct=is_correct,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(answer)

    db.commit()
