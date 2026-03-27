"""Given 使用者過去曾在某知識節點相關題目答錯 N 次 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.question import Question, QuestionType
from app.models.answer import Answer


@given('使用者 "{email}" 過去曾在 {node_keyword} 相關題目答錯 {count:d} 次')
def step_impl(context, email, node_keyword, count):
    db = context.db_session
    user_uuid = uuid.UUID(context.ids[email])

    # Store the historical pattern info for later verification
    context.memo["historical_wrong_node"] = node_keyword
    context.memo["historical_wrong_count"] = count

    # Create additional wrong answer records in the DB to represent history
    # Find a subject from existing exams
    exam = db.query(Exam).filter_by(user_id=user_uuid).first()
    if not exam:
        return

    resource_id = uuid.UUID(context.ids.get("default_resource", str(uuid.uuid4())))

    # Find matching node
    from app.models.knowledge_node import KnowledgeNode
    node = db.query(KnowledgeNode).filter(
        KnowledgeNode.name.contains(node_keyword)
    ).first()

    if not node:
        # Create a node for this keyword
        node = KnowledgeNode(
            resource_id=resource_id,
            name=f"{node_keyword} 歷史節點",
            depth=1,
            sort_order=0,
        )
        db.add(node)
        db.flush()

    # Create historical wrong answer records
    for i in range(count):
        hist_exam = Exam(
            user_id=user_uuid,
            subject_id=exam.subject_id,
            status=ExamStatus.SUBMITTED,
            total_questions=1,
            submitted_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
        )
        db.add(hist_exam)
        db.flush()

        hist_q = Question(
            exam_id=hist_exam.id,
            node_id=node.id,
            question_number=1,
            type=QuestionType.SINGLE_CHOICE,
            content=f"{node_keyword} 歷史錯題 {i+1}",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="A",
        )
        db.add(hist_q)
        db.flush()

        hist_a = Answer(
            exam_id=hist_exam.id,
            question_id=hist_q.id,
            user_id=user_uuid,
            selected_answer="B",
            is_correct=False,
        )
        db.add(hist_a)

    db.commit()
