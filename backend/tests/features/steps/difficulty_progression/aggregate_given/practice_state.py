"""Given 練習狀態相關步驟 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.question import Question


@given('使用者 "{email}" 正在練習節點 "{node_name}"（depth={depth:d}）')
def step_impl_practicing(context, email, node_name, depth):
    user_id = context.ids[email]
    node_id = context.ids[f"node_{node_name}"]
    context.memo[f"practice_node_{email}"] = node_name
    context.memo[f"practice_node_id_{email}"] = node_id
    context.memo[f"original_node_{email}"] = node_name
    context.memo[f"original_node_id_{email}"] = node_id
    context.memo[f"consecutive_wrong_{email}"] = 0
    context.memo[f"consecutive_correct_{email}"] = 0


@given('使用者連續答錯 {count:d} 題')
def step_impl_wrong_streak(context, count):
    # Find the current user from memo
    email = None
    for key in context.memo:
        if key.startswith("practice_node_") and not key.startswith("practice_node_id_"):
            email = key.replace("practice_node_", "")
            break

    if email:
        context.memo[f"consecutive_wrong_{email}"] = count
        context.memo[f"consecutive_correct_{email}"] = 0

        # Create actual answer records
        db = context.db_session
        user_id = uuid.UUID(context.ids[email])
        node_id = uuid.UUID(context.memo[f"practice_node_id_{email}"])

        subject_id = None
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                subject_id = uuid.UUID(val)
                break

        exam = Exam(
            user_id=user_id, subject_id=subject_id,
            status=ExamStatus.SUBMITTED, total_questions=count,
        )
        db.add(exam)
        db.flush()

        for i in range(count):
            q = Question(
                exam_id=exam.id, question_number=i + 1,
                content=f"練習題 #{i + 1}", correct_answer="A",
                option_a="A", option_b="B", option_c="C", option_d="D",
                node_id=node_id, source_type="historical",
            )
            db.add(q)
            db.flush()
            a = Answer(
                exam_id=exam.id, question_id=q.id, user_id=user_id,
                selected_answer="B", is_correct=False,
                answered_at=datetime.now(timezone.utc),
            )
            db.add(a)

        db.commit()


@given('使用者 "{email}" 已從 "{from_node}" 回溯到 "{to_node}"')
def step_impl_backtracked(context, email, from_node, to_node):
    context.memo[f"practice_node_{email}"] = to_node
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{to_node}"]
    context.memo[f"original_node_{email}"] = from_node
    context.memo[f"original_node_id_{email}"] = context.ids[f"node_{from_node}"]
    context.memo[f"consecutive_wrong_{email}"] = 0
    context.memo[f"consecutive_correct_{email}"] = 0
    context.memo[f"backtrack_count_{email}"] = context.memo.get(f"backtrack_count_{email}", 0) + 1


@given('使用者在 "{node_name}" 又連續答錯 {count:d} 題')
def step_impl_more_wrong(context, node_name, count):
    email = None
    for key in context.memo:
        if key.startswith("practice_node_") and not key.startswith("practice_node_id_"):
            email = key.replace("practice_node_", "")
            if context.memo[key] == node_name:
                break

    if email:
        context.memo[f"consecutive_wrong_{email}"] = count
        context.memo[f"consecutive_correct_{email}"] = 0

        db = context.db_session
        user_id = uuid.UUID(context.ids[email])
        node_id = uuid.UUID(context.ids[f"node_{node_name}"])

        subject_id = None
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                subject_id = uuid.UUID(val)
                break

        exam = Exam(
            user_id=user_id, subject_id=subject_id,
            status=ExamStatus.SUBMITTED, total_questions=count,
        )
        db.add(exam)
        db.flush()

        for i in range(count):
            q = Question(
                exam_id=exam.id, question_number=i + 1,
                content=f"補答錯題 #{i + 1}", correct_answer="A",
                option_a="A", option_b="B", option_c="C", option_d="D",
                node_id=node_id, source_type="historical",
            )
            db.add(q)
            db.flush()
            a = Answer(
                exam_id=exam.id, question_id=q.id, user_id=user_id,
                selected_answer="B", is_correct=False,
                answered_at=datetime.now(timezone.utc),
            )
            db.add(a)

        db.commit()


@given('使用者在 "{node_name}" 連續答錯 {count:d} 題')
def step_impl_wrong_at_node(context, node_name, count):
    email = None
    for key in context.memo:
        if key.startswith("practice_node_") and not key.startswith("practice_node_id_"):
            email = key.replace("practice_node_", "")
            break
    if email:
        context.memo[f"practice_node_{email}"] = node_name
        context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{node_name}"]
        context.memo[f"consecutive_wrong_{email}"] = count
        context.memo[f"consecutive_correct_{email}"] = 0


@given('使用者 "{email}" 已在根節點 "{node_name}"（depth={depth:d}）')
def step_impl_at_root(context, email, node_name, depth):
    context.memo[f"practice_node_{email}"] = node_name
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"original_node_{email}"] = node_name
    context.memo[f"original_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"consecutive_wrong_{email}"] = 0


@given('使用者 "{email}" 從 "{from_node}" 回溯到 "{to_node}"')
def step_impl_from_backtrack(context, email, from_node, to_node):
    context.memo[f"practice_node_{email}"] = to_node
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{to_node}"]
    context.memo[f"original_node_{email}"] = from_node
    context.memo[f"original_node_id_{email}"] = context.ids[f"node_{from_node}"]
    context.memo[f"backtrack_count_{email}"] = context.memo.get(f"backtrack_count_{email}", 0) + 1


@given('使用者在 "{node_name}" 連續答對 {count:d} 題')
def step_impl_correct_streak(context, node_name, count):
    email = None
    for key in context.memo:
        if key.startswith("practice_node_") and not key.startswith("practice_node_id_"):
            email = key.replace("practice_node_", "")
            break
    if email:
        context.memo[f"consecutive_correct_{email}"] = count
        context.memo[f"consecutive_wrong_{email}"] = 0

        db = context.db_session
        user_id = uuid.UUID(context.ids[email])
        node_id = uuid.UUID(context.ids[f"node_{node_name}"])

        subject_id = None
        for key, val in context.ids.items():
            if key.startswith("subject_name_"):
                subject_id = uuid.UUID(val)
                break

        exam = Exam(
            user_id=user_id, subject_id=subject_id,
            status=ExamStatus.SUBMITTED, total_questions=count,
        )
        db.add(exam)
        db.flush()

        for i in range(count):
            q = Question(
                exam_id=exam.id, question_number=i + 1,
                content=f"答對題 #{i + 1}", correct_answer="A",
                option_a="A", option_b="B", option_c="C", option_d="D",
                node_id=node_id, source_type="historical",
            )
            db.add(q)
            db.flush()
            a = Answer(
                exam_id=exam.id, question_id=q.id, user_id=user_id,
                selected_answer="A", is_correct=True,
                answered_at=datetime.now(timezone.utc),
            )
            db.add(a)

        db.commit()


@given('使用者 "{email}" 剛從 "{from_node}" 遞進回 "{to_node}"')
def step_impl_just_progressed(context, email, from_node, to_node):
    context.memo[f"practice_node_{email}"] = to_node
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{to_node}"]
    context.memo[f"original_node_{email}"] = to_node
    context.memo[f"original_node_id_{email}"] = context.ids[f"node_{to_node}"]
    context.memo[f"consecutive_wrong_{email}"] = 0
    context.memo[f"consecutive_correct_{email}"] = 0
