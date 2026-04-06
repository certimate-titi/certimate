"""Given 自適應練習相關 — Aggregate Given"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.question import Question


@given('使用者 "{email}" 正在進行自適應練習')
def step_impl_adaptive(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    nodes = db.query(KnowledgeNode).filter_by(subject_id=subject_id).all()
    if nodes:
        # Set to first leaf node
        leaf = [n for n in nodes if n.depth == max(nn.depth for nn in nodes)]
        target = leaf[0] if leaf else nodes[0]
        context.memo[f"practice_node_{email}"] = target.name
        context.memo[f"practice_node_id_{email}"] = str(target.id)
        context.memo[f"original_node_{email}"] = target.name
        context.memo[f"original_node_id_{email}"] = str(target.id)

    context.memo[f"consecutive_wrong_{email}"] = 0
    context.memo[f"consecutive_correct_{email}"] = 0

    # Create questions for practice
    exam = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=5,
    )
    db.add(exam)
    db.flush()

    for i, node in enumerate(nodes[:5]):
        q = Question(
            exam_id=exam.id, question_number=i + 1,
            content=f"自適應題目 {node.name} #{i + 1}",
            correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=node.id, source_type="historical",
        )
        db.add(q)

    db.commit()
    context.memo[f"adaptive_exam_id_{email}"] = str(exam.id)


@given('使用者 "{email}" 完成一輪自適應練習，軌跡如下：')
def step_impl_trail(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    exam = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=7,
    )
    db.add(exam)
    db.flush()

    q_num = 0
    for row in context.table:
        node_name = row["節點"]
        action = row["動作"]
        result = row["結果"]

        node_id = uuid.UUID(context.ids[f"node_{node_name}"])

        # Parse result like "答錯 ×2" or "答對 ×3"
        count = 2
        is_correct = "答對" in result
        if "×" in result:
            count = int(result.split("×")[1].strip())

        for i in range(count):
            q_num += 1
            q = Question(
                exam_id=exam.id, question_number=q_num,
                content=f"軌跡題目 {node_name} #{q_num}",
                correct_answer="A",
                option_a="A", option_b="B", option_c="C", option_d="D",
                node_id=node_id, source_type="historical",
            )
            db.add(q)
            db.flush()
            a = Answer(
                exam_id=exam.id, question_id=q.id, user_id=user_id,
                selected_answer="A" if is_correct else "B",
                is_correct=is_correct,
                answered_at=datetime.now(timezone.utc),
            )
            db.add(a)

    # Update exam total_questions
    exam.total_questions = q_num

    db.commit()
    context.memo[f"trail_exam_id_{email}"] = str(exam.id)


@given('使用者 "{email}" 節點 "{node_name}" 原本為 red（答對率 {rate:d}%）')
def step_impl_red_node(context, email, node_name, rate):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    mastery = NodeMastery(
        user_id=user_id, node_id=node_id,
        correct_count=rate, total_count=100,
        mastery_rate=Decimal(str(rate)), color="red",
    )
    db.add(mastery)
    db.commit()


@given('使用者在回溯練習中於 "{node_name}" 額外答對 {count:d} 題')
def step_impl_extra_correct(context, node_name, count):
    db = context.db_session
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    # Find user
    email = None
    for key in context.ids:
        if "@" in key:
            email = key
            break

    user_id = uuid.UUID(context.ids[email])

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
            content=f"額外答對 #{i + 1}", correct_answer="A",
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
