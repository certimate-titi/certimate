"""Given 考試錯題資料建立 — Aggregate Given"""

import uuid
from behave import given, use_step_matcher

use_step_matcher("re")


@given(r'考試 (?P<exam_id>\d+) 中學員答錯以下題目：')
def step_impl(context, exam_id):
    """Create question + wrong answer records for an exam."""
    from app.models.question import Question
    from app.models.answer import Answer

    exam_int_id = int(exam_id)
    exam_uuid = uuid.UUID(int=exam_int_id)

    # Find the student who owns this exam
    from app.models.exam import Exam
    exam = context.db_session.query(Exam).filter_by(id=exam_uuid).first()
    assert exam is not None, f"Exam {exam_id} not found in DB"

    # First pass: create all questions and flush to DB to satisfy FK constraints
    questions_info = []
    for row in context.table:
        q_number = int(row["題號"])
        content = row["題目內容"]
        student_answer = row["學生作答"]
        correct_answer = row["正確答案"]
        difficulty = row["難度"]
        explanation = row["解析"]

        q_id = uuid.uuid4()
        question = Question(
            id=q_id,
            exam_id=exam_uuid,
            question_number=q_number,
            content=content,
            correct_answer=correct_answer,
            difficulty=difficulty,
            explanation=explanation,
        )
        context.db_session.add(question)
        questions_info.append({
            "q_id": q_id,
            "q_number": q_number,
            "content": content,
            "student_answer": student_answer,
            "correct_answer": correct_answer,
            "difficulty": difficulty,
            "explanation": explanation,
        })

    # Flush questions so they exist in DB before creating answers (FK constraint)
    context.db_session.flush()

    # Second pass: create answers referencing the now-persisted questions
    wrong_answers_data = []
    for info in questions_info:
        answer = Answer(
            id=uuid.uuid4(),
            exam_id=exam_uuid,
            question_id=info["q_id"],
            user_id=exam.user_id,
            selected_answer=info["student_answer"],
            is_correct=False,
        )
        context.db_session.add(answer)

        wrong_answers_data.append({
            "question_number": info["q_number"],
            "content": info["content"],
            "student_answer": info["student_answer"],
            "correct_answer": info["correct_answer"],
            "difficulty": info["difficulty"],
            "explanation": info["explanation"],
        })

    context.db_session.commit()
    context.memo.setdefault("exam_wrong_answers", {})[str(exam_int_id)] = wrong_answers_data


use_step_matcher("parse")
