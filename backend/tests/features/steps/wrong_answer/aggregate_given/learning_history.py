"""Given 使用者過去 N 天完成 M 次測驗 / 弱點節點 — Aggregate Given"""

import uuid
from datetime import datetime, timedelta, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.question import Question, QuestionType
from app.models.answer import Answer
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope


@given('使用者 "{email}" 過去 {days:d} 天完成 {count:d} 次測驗')
def step_impl(context, email, days, count):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    # Find an existing subject for this user
    existing_exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    subject_id = existing_exam.subject_id if existing_exam else None

    if not subject_id:
        subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    now = datetime.now(timezone.utc)
    for i in range(count):
        exam = Exam(
            user_id=user_uuid,
            subject_id=subject_id,
            status=ExamStatus.SUBMITTED,
            total_questions=10,
            submitted_at=now - timedelta(days=days - i * (days // max(count, 1))),
            started_at=now - timedelta(days=days - i * (days // max(count, 1))),
        )
        db.add(exam)

    db.commit()
    context.memo["learning_history_exam_count"] = count


@given('使用者 "{email}" 的弱點節點為 "{topic1}" 和 "{topic2}"')
def step_impl_weak_topics(context, email, topic1, topic2):
    """在 DB 中建立弱點知識節點的錯題記錄。"""
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    existing_exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    subject_id = existing_exam.subject_id if existing_exam else None
    if not subject_id:
        subject_id = uuid.UUID(context.ids.get("default_subject", str(uuid.uuid4())))

    # Ensure resource exists
    resource_id_str = context.ids.get("default_resource")
    if not resource_id_str:
        res = Resource(
            user_id=user_uuid,
            subject_id=subject_id,
            name="weak_topic_resource.pdf",
            type=ResourceType.PDF,
            status=ResourceStatus.COMPLETED,
            scope=ResourceScope.PERSONAL,
        )
        db.add(res)
        db.flush()
        context.ids["default_resource"] = str(res.id)
        resource_id_str = str(res.id)

    resource_id = uuid.UUID(resource_id_str)

    for topic in [topic1, topic2]:
        node_key = f"node_{topic}"
        if node_key not in context.ids:
            node = KnowledgeNode(
                resource_id=resource_id,
                name=topic,
                depth=1,
                sort_order=0,
            )
            db.add(node)
            db.flush()
            context.ids[node_key] = str(node.id)

        node_id = uuid.UUID(context.ids[node_key])

        # Create wrong answer records for this topic
        for i in range(3):
            weak_exam = Exam(
                user_id=user_uuid,
                subject_id=subject_id,
                status=ExamStatus.SUBMITTED,
                total_questions=1,
                submitted_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
            )
            db.add(weak_exam)
            db.flush()

            q = Question(
                exam_id=weak_exam.id,
                node_id=node_id,
                question_number=1,
                type=QuestionType.SINGLE_CHOICE,
                content=f"{topic} 弱點題目 {i+1}",
                option_a="A", option_b="B", option_c="C", option_d="D",
                correct_answer="A",
            )
            db.add(q)
            db.flush()

            a = Answer(
                exam_id=weak_exam.id,
                question_id=q.id,
                user_id=user_uuid,
                selected_answer="B",
                is_correct=False,
            )
            db.add(a)

    db.commit()
    context.memo["weak_topics"] = [topic1, topic2]
