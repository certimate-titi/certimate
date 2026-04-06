"""Given 使用者已完成多次考試 — Aggregate Given"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from behave import given

from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.node_mastery import NodeMastery
from app.models.question import Question
from app.models.knowledge_node import KnowledgeNode


@given('使用者 "{email}" 已完成多次考試，各節點掌握度已更新')
def step_impl(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    # Find subject
    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    # Get all nodes for subject
    nodes = db.query(KnowledgeNode).filter_by(subject_id=subject_id).all()

    # Create mastery for each node (if not exists)
    for i, node in enumerate(nodes):
        existing = db.query(NodeMastery).filter_by(
            user_id=user_id, node_id=node.id
        ).first()
        if existing:
            continue

        rate = 30 + (i * 15) % 70  # Spread between 30-100
        if rate < 60:
            color = "red"
        elif rate < 80:
            color = "orange"
        else:
            color = "green"

        mastery = NodeMastery(
            user_id=user_id,
            node_id=node.id,
            correct_count=rate,
            total_count=100,
            mastery_rate=Decimal(str(rate)),
            color=color,
        )
        db.add(mastery)

    db.commit()


@given('使用者 "{email}" 已在本週和上週分別完成考試')
def step_impl_time_periods(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    nodes = db.query(KnowledgeNode).filter_by(subject_id=subject_id).all()
    if not nodes:
        return

    now = datetime.now(timezone.utc)
    last_week = now - timedelta(days=7)

    # Create last week's exam
    exam_lw = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=5,
    )
    db.add(exam_lw)
    db.flush()

    for i in range(5):
        node = nodes[i % len(nodes)]
        q = Question(
            exam_id=exam_lw.id, question_number=i + 1,
            content=f"上週題目 #{i + 1}", correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=node.id, source_type="historical",
        )
        db.add(q)
        db.flush()
        a = Answer(
            exam_id=exam_lw.id, question_id=q.id, user_id=user_id,
            selected_answer="B", is_correct=False,
            answered_at=last_week,
        )
        db.add(a)

    # Create this week's exam
    exam_tw = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=5,
    )
    db.add(exam_tw)
    db.flush()

    for i in range(5):
        node = nodes[i % len(nodes)]
        q = Question(
            exam_id=exam_tw.id, question_number=i + 1,
            content=f"本週題目 #{i + 1}", correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=node.id, source_type="historical",
        )
        db.add(q)
        db.flush()
        a = Answer(
            exam_id=exam_tw.id, question_id=q.id, user_id=user_id,
            selected_answer="A", is_correct=True,
            answered_at=now,
        )
        db.add(a)

    db.commit()
    context.memo["this_week_exam_id"] = str(exam_tw.id)
    context.memo["last_week_exam_id"] = str(exam_lw.id)


@given('使用者 "{email}" 已有完整的錯題地圖資料')
def step_impl_complete_map(context, email):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])

    subject_id = None
    for key, val in context.ids.items():
        if key.startswith("subject_name_"):
            subject_id = uuid.UUID(val)
            break

    nodes = db.query(KnowledgeNode).filter_by(subject_id=subject_id).all()

    # Create mastery for leaf nodes only
    rates = {"信託財產獨立性原則": 30, "忠實義務": 70, "金錢信託": 85}
    for node in nodes:
        existing = db.query(NodeMastery).filter_by(
            user_id=user_id, node_id=node.id
        ).first()
        if existing:
            continue

        rate = rates.get(node.name, 55)
        if rate < 60:
            color = "red"
        elif rate < 80:
            color = "orange"
        else:
            color = "green"

        mastery = NodeMastery(
            user_id=user_id, node_id=node.id,
            correct_count=rate, total_count=100,
            mastery_rate=Decimal(str(rate)),
            color=color,
        )
        db.add(mastery)

    # Create some wrong answers for exam creation
    exam = Exam(
        user_id=user_id, subject_id=subject_id,
        status=ExamStatus.SUBMITTED, total_questions=10,
    )
    db.add(exam)
    db.flush()

    target_node = nodes[0] if nodes else None
    for i in range(10):
        q = Question(
            exam_id=exam.id, question_number=i + 1,
            content=f"完整地圖題目 #{i + 1}", correct_answer="A",
            option_a="A", option_b="B", option_c="C", option_d="D",
            node_id=target_node.id if target_node else None,
            source_type="historical",
        )
        db.add(q)
        db.flush()
        a = Answer(
            exam_id=exam.id, question_id=q.id, user_id=user_id,
            selected_answer="B" if i < 7 else "A",
            is_correct=(i >= 7),
            answered_at=datetime.now(timezone.utc),
        )
        db.add(a)

    db.commit()
