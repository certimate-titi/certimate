"""租戶 "{slug}" 的學生完成一份考試並留下 answers 記錄."""

import uuid
from behave import given
from app.models.exam import Exam
from app.models.answer import Answer
from app.models.question import Question


@given('租戶 "{slug}" 的學生完成一份考試並留下 answers 記錄')
def step_impl(context, slug):
    """為租戶建立 exam + answer 記錄（含 tenant_id）。"""
    tenant_id = uuid.UUID(context.ids.get(slug) or context.memo.get(f"tenant_id_{slug}"))
    user_id = uuid.UUID(context.ids.get(f"user_{slug}"))

    # 取用已有的 subject
    subject_key = f"subject_{slug}"
    if subject_key not in context.ids:
        from app.models.subject import Subject
        subject = Subject(
            id=uuid.uuid4(),
            name=f"Subject for {slug}",
            category_id=None,
        )
        context.db_session.merge(subject)
        context.db_session.commit()
        context.ids[subject_key] = str(subject.id)
    subject_id = uuid.UUID(context.ids[subject_key])

    # 建立 exam
    exam = Exam(
        id=uuid.uuid4(),
        user_id=user_id,
        subject_id=subject_id,
        mode="practice",
        question_count=1,
        status="completed",
        tenant_id=tenant_id,
    )
    context.db_session.merge(exam)
    context.db_session.commit()

    # 建立 question
    question = Question(
        id=uuid.uuid4(),
        subject_id=subject_id,
        question_text="Test question?",
        options_json=["A", "B", "C", "D"],
        answer="A",
        difficulty="easy",
        tenant_id=tenant_id,
    )
    context.db_session.merge(question)
    context.db_session.commit()

    # 建立 answer
    answer = Answer(
        id=uuid.uuid4(),
        exam_id=exam.id,
        question_id=question.id,
        user_id=user_id,
        selected_answer="A",
        is_correct=True,
        tenant_id=tenant_id,
    )
    context.db_session.merge(answer)
    context.db_session.commit()

    context.ids[f"exam_{slug}"] = str(exam.id)
    context.ids[f"answer_{slug}"] = str(answer.id)
