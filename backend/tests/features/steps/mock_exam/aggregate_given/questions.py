"""Given 測驗 N 包含以下題目 — Aggregate Given"""

import uuid

from behave import given

from app.models.question import Question, QuestionType


TYPE_MAP = {
    "單選": QuestionType.SINGLE_CHOICE,
    "多選": QuestionType.MULTIPLE_CHOICE,
    "填空": QuestionType.FILL_IN,
}


@given('測驗 {exam_id:d} 包含以下題目：')
def step_impl(context, exam_id):
    db = context.db_session
    exam_uuid = uuid.UUID(int=exam_id)

    for row in context.table:
        q_id_int = int(row["題目 ID"])
        q_number = int(row["題號"])
        content = row["題目內容"]
        option_a = row["選項A"]
        option_b = row["選項B"]
        option_c = row["選項C"]
        option_d = row["選項D"]

        q = Question(
            id=uuid.UUID(int=q_id_int),
            exam_id=exam_uuid,
            question_number=q_number,
            type=QuestionType.SINGLE_CHOICE,
            content=content,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer="A",
        )
        db.add(q)

    db.commit()

    # Store question IDs for later use
    for row in context.table:
        q_id_int = int(row["題目 ID"])
        context.ids[f"question_{q_id_int}"] = str(uuid.UUID(int=q_id_int))


@given('測驗 {exam_id:d} 包含以下數學工程題目：')
def step_impl_math(context, exam_id):
    db = context.db_session
    exam_uuid = uuid.UUID(int=exam_id)

    for row in context.table:
        q_id_int = int(row["題目 ID"])
        q_number = int(row["題號"])
        q_type_raw = row["題型"]
        content = row["題目內容（含 KaTeX）"]
        option_a = row["選項A"] if row["選項A"] != "null" else None
        option_b = row["選項B"] if row["選項B"] != "null" else None
        option_c = row["選項C"] if row["選項C"] != "null" else None
        option_d = row["選項D"] if row["選項D"] != "null" else None

        q = Question(
            id=uuid.UUID(int=q_id_int),
            exam_id=exam_uuid,
            question_number=q_number,
            type=TYPE_MAP.get(q_type_raw, QuestionType.SINGLE_CHOICE),
            content=content,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer="A",
        )
        db.add(q)

    db.commit()

    for row in context.table:
        q_id_int = int(row["題目 ID"])
        context.ids[f"question_{q_id_int}"] = str(uuid.UUID(int=q_id_int))
