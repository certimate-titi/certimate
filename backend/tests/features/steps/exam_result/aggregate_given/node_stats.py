"""Given 測驗 N 包含以下知識節點答對率 — Aggregate Given

Stores node-level stats in context.memo for the exam result service to use.
We create Question + Answer records to represent node-level stats.
"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question, QuestionType
from app.models.answer import Answer


@given('測驗 {exam_id:d} 包含以下知識節點答對率：')
def step_impl(context, exam_id):
    db = context.db_session
    exam_uuid = uuid.UUID(int=exam_id)

    # Get exam's user_id
    from app.models.exam import Exam
    exam = db.query(Exam).filter_by(id=exam_uuid).first()
    user_id = exam.user_id

    # Get or create a resource for nodes
    if "default_resource" not in context.ids:
        from app.models.resource import Resource, ResourceType, ResourceStatus, ResourceScope
        subject_id = uuid.UUID(context.ids["default_subject"])
        res = Resource(
            user_id=user_id,
            subject_id=subject_id,
            name="test.pdf",
            type=ResourceType.PDF,
            status=ResourceStatus.COMPLETED,
            scope=ResourceScope.PERSONAL,
        )
        db.add(res)
        db.flush()
        context.ids["default_resource"] = str(res.id)

    resource_id = uuid.UUID(context.ids["default_resource"])

    q_counter = 1000  # Start from a high number to avoid collision
    for row in context.table:
        node_name = row["節點名稱"]
        correct = int(row["答對數"])
        total = int(row["出題數"])

        # Create knowledge node
        node = KnowledgeNode(
            resource_id=resource_id,
            name=node_name,
            depth=1,
            sort_order=0,
        )
        db.add(node)
        db.flush()

        # Create questions and answers for this node
        for i in range(total):
            q_counter += 1
            q = Question(
                exam_id=exam_uuid,
                node_id=node.id,
                question_number=q_counter,
                type=QuestionType.SINGLE_CHOICE,
                content=f"Question about {node_name} #{i+1}",
                option_a="A", option_b="B", option_c="C", option_d="D",
                correct_answer="A",
            )
            db.add(q)
            db.flush()

            is_correct = i < correct
            answer = Answer(
                exam_id=exam_uuid,
                question_id=q.id,
                user_id=user_id,
                selected_answer="A" if is_correct else "B",
                is_correct=is_correct,
            )
            db.add(answer)

    db.commit()
