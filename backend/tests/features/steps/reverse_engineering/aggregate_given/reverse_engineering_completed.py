"""Given 管理員已對考科啟動逆向工程且處理完成 / ���完成考綱逆向工程 — Aggregate Given"""

import uuid
from decimal import Decimal

from behave import given

from app.models.reverse_engineering_task import ReverseEngineeringTask
from app.models.knowledge_node import KnowledgeNode


@given('管理員已對考科 "{subject_name}" 啟動逆向工程且處理完成')
def step_impl(context, subject_name):
    _create_completed_reverse_engineering(context, subject_name)


@given('考科 "{subject_name}" 已完成考綱逆向工程')
def step_impl_completed(context, subject_name):
    _create_completed_reverse_engineering(context, subject_name)


@given('考科 "{subject_name}" 已完成考綱逆向工程（{count:d} 題）')
def step_impl_completed_with_count(context, subject_name, count):
    _create_completed_reverse_engineering(context, subject_name, total_questions=count)


def _create_completed_reverse_engineering(context, subject_name, total_questions=None):
    db = context.db_session

    subject_id_str = context.ids.get(f"subject_name_{subject_name}")
    if not subject_id_str:
        raise KeyError(f"找不到考科 '{subject_name}'，請先建立考科")
    subject_id = uuid.UUID(subject_id_str)

    # Find admin user
    admin_id = None
    for key, val in context.ids.items():
        if "@" in key:
            admin_id = uuid.UUID(val)
            break
    if not admin_id:
        raise KeyError("找不到任何使用者")

    if total_questions is None:
        total_questions = context.memo.get(f"total_questions_{subject_name}", 180)

    # Create completed task
    task = ReverseEngineeringTask(
        subject_id=subject_id,
        triggered_by=admin_id,
        status="COMPLETED",
        total_questions=total_questions,
        node_count=12,
        coverage_rate=Decimal("95.00"),
        max_depth=3,
        orphan_node_count=0,
        reliability="green",
    )
    db.add(task)
    db.flush()
    context.ids[f"re_task_{subject_name}"] = str(task.id)

    # Create knowledge tree structure (3 levels)
    # Level 1: Core topics
    topics = [
        ("信託法規", [
            ("信託契約", ["信託契約要素", "信託財產獨立性原則"]),
            ("受託人義務", ["忠實義務", "善良管理人注意義務"]),
        ]),
        ("信託實務", [
            ("金錢信託", []),
            ("有價證券信託", []),
        ]),
        ("信託稅制", [
            ("信託課稅原則", []),
        ]),
    ]

    sort = 0
    for topic_name, sub_topics in topics:
        node_l1 = KnowledgeNode(
            subject_id=subject_id,
            name=topic_name,
            depth=1,
            sort_order=sort,
            exam_frequency="high",
            source_origin="reverse_engineering",
        )
        db.add(node_l1)
        db.flush()
        context.ids[f"node_{topic_name}"] = str(node_l1.id)
        sort += 1

        for sub_name, details in sub_topics:
            node_l2 = KnowledgeNode(
                subject_id=subject_id,
                parent_id=node_l1.id,
                name=sub_name,
                depth=2,
                sort_order=sort,
                exam_frequency="medium",
                source_origin="reverse_engineering",
            )
            db.add(node_l2)
            db.flush()
            context.ids[f"node_{sub_name}"] = str(node_l2.id)
            sort += 1

            for detail_name in details:
                node_l3 = KnowledgeNode(
                    subject_id=subject_id,
                    parent_id=node_l2.id,
                    name=detail_name,
                    depth=3,
                    sort_order=sort,
                    exam_frequency="low",
                    source_origin="reverse_engineering",
                )
                db.add(node_l3)
                db.flush()
                context.ids[f"node_{detail_name}"] = str(node_l3.id)
                sort += 1

    db.commit()

    # Create questions if they don't already exist and total_questions is specified
    _ensure_questions_exist(context, subject_name, subject_id, admin_id, total_questions)

    # Map questions to nodes if questions exist
    _map_questions_to_nodes(context, subject_name, subject_id)


def _ensure_questions_exist(context, subject_name, subject_id, admin_id, total_questions):
    """Create questions if none exist for this subject."""
    db = context.db_session
    from app.models.question import Question
    from app.models.exam import Exam, ExamStatus

    existing_count = (
        db.query(Question)
        .join(Exam, Question.exam_id == Exam.id)
        .filter(Exam.subject_id == subject_id)
        .count()
    )
    if existing_count > 0:
        return

    # Create exam + questions
    exam = Exam(
        user_id=admin_id,
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=total_questions,
    )
    db.add(exam)
    db.flush()

    for i in range(total_questions):
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


def _map_questions_to_nodes(context, subject_name, subject_id):
    """Map existing questions to knowledge nodes."""
    db = context.db_session
    from app.models.question import Question
    from app.models.exam import Exam

    # Get all questions for this subject
    questions = (
        db.query(Question)
        .join(Exam, Question.exam_id == Exam.id)
        .filter(Exam.subject_id == subject_id)
        .all()
    )

    if not questions:
        return

    # Get all leaf/detail nodes
    nodes = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject_id)
        .all()
    )
    if not nodes:
        return

    # Distribute questions across nodes (round-robin)
    for i, q in enumerate(questions):
        q.node_id = nodes[i % len(nodes)].id

    db.commit()
