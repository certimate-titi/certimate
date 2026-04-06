"""Given 考科已匯入 N 題考古題 / 僅有 N 題考古題 — Aggregate Given"""

import uuid

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.models.resource import Resource, ResourceStatus


@given('考科 "{subject_name}" 已匯入 {count:d} 題考古題')
def step_impl(context, subject_name, count):
    _create_historical_questions(context, subject_name, count)


@given('考科 "{subject_name}" 僅有 {count:d} 題考古題')
def step_impl_few(context, subject_name, count):
    _create_historical_questions(context, subject_name, count)


@given('考科 "{subject_name}" 新增 {count:d} 題考古題')
def step_impl_additional(context, subject_name, count):
    _create_historical_questions(context, subject_name, count, additional=True)


def _create_historical_questions(context, subject_name, count, additional=False):
    db = context.db_session

    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id_str:
        raise KeyError(f"找不到考科 '{subject_name}'，請先建立考科")
    subject_id = uuid.UUID(subject_id_str)

    # Find a user to own the exam (use first admin)
    owner_id = None
    for key, val in context.ids.items():
        if "@" in key:
            owner_id = uuid.UUID(val)
            break
    if not owner_id:
        raise KeyError("找不到任何使用者，請先建立使用者帳號")

    # Create exam
    exam_key = f"historical_exam_{subject_name}"
    if additional and exam_key in context.ids:
        # For additional questions, create another exam
        exam_key = f"historical_exam_{subject_name}_additional"

    exam = Exam(
        user_id=owner_id,
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=count,
    )
    db.add(exam)
    db.flush()
    context.ids[exam_key] = str(exam.id)

    # Create questions
    for i in range(count):
        q = Question(
            exam_id=exam.id,
            question_number=i + 1,
            content=f"考古題 {subject_name} #{i + 1}",
            correct_answer="A",
            option_a="選項A",
            option_b="選項B",
            option_c="選項C",
            option_d="選項D",
            source_type="historical",
            historical_source=f"{subject_name}_exam_2024",
        )
        db.add(q)

    db.commit()

    # Track total questions for subject
    total_key = f"total_questions_{subject_name}"
    prev = context.memo.get(total_key, 0)
    context.memo[total_key] = prev + count
