"""When 使用者在 AI 教練視窗輸入 (without exam/question context) — Command"""

import uuid

from behave import when


@when('使用者 "{email}" 在 AI 教練視窗輸入 "{message}"')
def step_impl(context, email, message):
    """AI 教練提問（使用 memo 中的測驗/題目上下文或預設）。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    from app.models.exam import Exam
    from app.models.question import Question
    from app.models.answer import Answer
    db = context.db_session
    user_uuid = uuid.UUID(user_id)

    # Try user's own exam first, then fall back to any exam with wrong answers
    exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    question = None
    if exam:
        question = (
            db.query(Question)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Question.exam_id == exam.id)
            .filter(Answer.is_correct == False)  # noqa: E712
            .first()
        )

    if not question:
        # Fallback: find any exam with wrong answers in the DB
        row = (
            db.query(Exam, Question)
            .join(Question, Question.exam_id == Exam.id)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Answer.is_correct == False)  # noqa: E712
            .first()
        )
        if row:
            exam, question = row

    if not exam or not question:
        response = context.api_client.post(
            "/api/v1/wrong-answers/00000000-0000-0000-0000-000000000000/questions/00000000-0000-0000-0000-000000000000/coach",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": message},
        )
    else:
        response = context.api_client.post(
            f"/api/v1/wrong-answers/{exam.id}/questions/{question.id}/coach",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": message},
        )

    context.last_response = response


@when('使用者 "{email}" 在 AI 教練視窗提問')
def step_impl_generic(context, email):
    """AI 教練通用提問（預設訊息）。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    from app.models.exam import Exam
    from app.models.question import Question
    from app.models.answer import Answer
    db = context.db_session
    user_uuid = uuid.UUID(user_id)

    exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    question = None
    if exam:
        question = (
            db.query(Question)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Question.exam_id == exam.id)
            .filter(Answer.is_correct == False)  # noqa: E712
            .first()
        )

    if not question:
        row = (
            db.query(Exam, Question)
            .join(Question, Question.exam_id == Exam.id)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Answer.is_correct == False)  # noqa: E712
            .first()
        )
        if row:
            exam, question = row

    if exam and question:
        response = context.api_client.post(
            f"/api/v1/wrong-answers/{exam.id}/questions/{question.id}/coach",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "請幫我解釋這題"},
        )
    else:
        response = context.api_client.post(
            "/api/v1/wrong-answers/00000000-0000-0000-0000-000000000000/questions/00000000-0000-0000-0000-000000000000/coach",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "請幫我解釋這題"},
        )

    context.last_response = response


@when('使用者 "{email}" 再次提出超出範圍的問題')
def step_impl_out_of_scope_again(context, email):
    """再次提出超綱問題（觸發冷卻）。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    exam_id = context.memo.get("cooldown_exam_id")
    question_id = context.memo.get("cooldown_question_id")

    if not exam_id or not question_id:
        from app.models.exam import Exam
        from app.models.question import Question
        db = context.db_session
        user_uuid = uuid.UUID(user_id)
        exam = db.query(Exam).filter_by(user_id=user_uuid).first()
        if exam:
            question = db.query(Question).filter_by(exam_id=exam.id).first()
            exam_id = str(exam.id)
            question_id = str(question.id) if question else None

    response = context.api_client.post(
        f"/api/v1/wrong-answers/{exam_id}/questions/{question_id}/coach",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "幫我寫一首詩"},
    )
    context.last_response = response


@when('使用者 "{email}" 開啟 AI 教練對話視窗')
def step_impl_open_coach(context, email):
    """開啟 AI 教練對話視窗 — 取得免責聲明。"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    from app.models.exam import Exam
    from app.models.question import Question
    from app.models.answer import Answer
    db = context.db_session
    user_uuid = uuid.UUID(user_id)

    exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    question = None
    if exam:
        question = (
            db.query(Question)
            .join(Answer, Answer.question_id == Question.id)
            .filter(Question.exam_id == exam.id)
            .filter(Answer.is_correct == False)  # noqa: E712
            .first()
        )

    if exam and question:
        response = context.api_client.get(
            f"/api/v1/wrong-answers/{exam.id}/questions/{question.id}/coach",
            headers={"Authorization": f"Bearer {token}"},
        )
    else:
        response = context.api_client.get(
            "/api/v1/wrong-answers/00000000-0000-0000-0000-000000000000/questions/00000000-0000-0000-0000-000000000000/coach",
            headers={"Authorization": f"Bearer {token}"},
        )

    context.last_response = response
