"""Given 回溯/遞進觸發條件 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.node_mastery import NodeMastery
from app.models.question import Question
from decimal import Decimal


@given('系統的回溯觸發條件為「連續答錯 {count:d} 題」')
def step_impl_backtrack_threshold(context, count):
    context.memo["backtrack_wrong_threshold"] = count


@given('使用者 "{email}" 在節點 "{node_name}" 答對 {correct:d} 題後答錯 {wrong:d} 題')
def step_impl_mixed(context, email, node_name, correct, wrong):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    context.memo[f"practice_node_{email}"] = node_name
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"original_node_{email}"] = node_name
    context.memo[f"original_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"consecutive_wrong_{email}"] = wrong
    context.memo[f"consecutive_correct_{email}"] = 0

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    total = correct + wrong
    exam = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=total,
    )
    db.add(exam)
    db.flush()

    for i in range(total):
        q = Question(
            exam_id=exam.id, question_number=i + 1,
            content=f"混合題 #{i + 1}", correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=node_id, source_type="historical",
        )
        db.add(q)
        db.flush()
        is_correct = i < correct
        a = Answer(
            exam_id=exam.id, question_id=q.id, user_id=user_id,
            selected_answer="A" if is_correct else "B",
            is_correct=is_correct,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(a)

    db.commit()


@given('系統的回溯觸發條件包含「節點答對率 < {threshold:d}%」')
def step_impl_rate_threshold(context, threshold):
    context.memo["backtrack_rate_threshold"] = threshold


@given('使用者 "{email}" 在節點 "{node_name}" 的答對率為 {rate:d}%（答對 {correct:d} / 總 {total:d}）')
def step_impl_rate(context, email, node_name, rate, correct, total):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    context.memo[f"practice_node_{email}"] = node_name
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"original_node_{email}"] = node_name
    context.memo[f"original_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"consecutive_wrong_{email}"] = 0

    # Create mastery record
    mastery = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        correct_count=correct,
        total_count=total,
        mastery_rate=Decimal(str(rate)),
        color="red" if rate < 60 else "orange",
    )
    db.add(mastery)

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    exam = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=total,
    )
    db.add(exam)
    db.flush()

    for i in range(total):
        q = Question(
            exam_id=exam.id, question_number=i + 1,
            content=f"答對率題 #{i + 1}", correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=node_id, source_type="historical",
        )
        db.add(q)
        db.flush()
        is_correct = i < correct
        a = Answer(
            exam_id=exam.id, question_id=q.id, user_id=user_id,
            selected_answer="A" if is_correct else "B",
            is_correct=is_correct,
            answered_at=datetime.now(timezone.utc),
        )
        db.add(a)

    db.commit()


@given('系統的遞進觸發條件為「連續答對 {count:d} 題」')
def step_impl_progress_threshold(context, count):
    context.memo["progress_correct_threshold"] = count


@given('使用者 "{email}" 在父節點 "{node_name}" 答對 {count:d} 題')
def step_impl_parent_correct(context, email, node_name, count):
    context.memo[f"practice_node_{email}"] = node_name
    context.memo[f"practice_node_id_{email}"] = context.ids[f"node_{node_name}"]
    context.memo[f"consecutive_correct_{email}"] = count
    context.memo[f"consecutive_wrong_{email}"] = 0
