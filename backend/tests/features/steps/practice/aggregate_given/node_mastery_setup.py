"""Given 節點掌握度 fixture — Epic 3 Node Mastery Pipeline."""

import uuid
from decimal import Decimal

from behave import given

from app.models.user import User
from app.models.subject import Subject
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.question import Question, DifficultyLevel, QuestionType
from app.models.resource import Resource, ResourceType, ResourceStatus


@given('使用者 "{email}" 的節點 "{node_name}" 掌握度為 {rate:d}%')
def step_user_node_mastery(context, email, node_name, rate):
    """建立使用者、科目、節點、父節點、NodeMastery 與一題練習題。"""
    db = context.db_session
    user = db.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="AWS SAA", institution_id=None, category_id=None)
        db.add(subject)
        db.flush()

    parent = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject.id, KnowledgeNode.depth == 0)
        .first()
    )
    if not parent:
        parent = KnowledgeNode(
            subject_id=subject.id, resource_id=None,
            name="AWS 知識樹", depth=0, sort_order=0,
        )
        db.add(parent)
        db.flush()

    node = (
        db.query(KnowledgeNode)
        .filter(KnowledgeNode.subject_id == subject.id, KnowledgeNode.name == node_name)
        .first()
    )
    if not node:
        node = KnowledgeNode(
            subject_id=subject.id, resource_id=None,
            parent_id=parent.id, name=node_name, depth=1, sort_order=0,
        )
        db.add(node)
        db.flush()

    # NodeMastery for target node
    mastery = (
        db.query(NodeMastery)
        .filter(NodeMastery.user_id == user.id, NodeMastery.node_id == node.id)
        .first()
    )
    if not mastery:
        mastery = NodeMastery(user_id=user.id, node_id=node.id)
        db.add(mastery)
    mastery.mastery_rate = Decimal(str(rate))
    mastery.correct_count = rate
    mastery.total_count = 100

    # NodeMastery for parent (initialize at same rate)
    parent_mastery = (
        db.query(NodeMastery)
        .filter(NodeMastery.user_id == user.id, NodeMastery.node_id == parent.id)
        .first()
    )
    if not parent_mastery:
        parent_mastery = NodeMastery(user_id=user.id, node_id=parent.id)
        db.add(parent_mastery)
    parent_mastery.mastery_rate = Decimal(str(rate))
    parent_mastery.correct_count = rate
    parent_mastery.total_count = 100

    # One practice question on the node (correct answer B)
    question = (
        db.query(Question)
        .filter(Question.node_id == node.id)
        .first()
    )
    if not question:
        resource = (
            db.query(Resource)
            .filter(Resource.user_id == user.id, Resource.subject_id == subject.id)
            .first()
        )
        if not resource:
            resource = Resource(
                user_id=user.id, subject_id=subject.id,
                name="練習題來源.pdf", type=ResourceType.PDF,
                status=ResourceStatus.COMPLETED,
            )
            db.add(resource)
            db.flush()

        question = Question(
            node_id=node.id,
            source_resource_id=resource.id,
            content=f"{node_name} 的練習題",
            option_a="A", option_b="B", option_c="C", option_d="D",
            correct_answer="B",
            explanation="B 是正解",
            difficulty=DifficultyLevel.MEDIUM,
            type=QuestionType.SINGLE_CHOICE,
            question_number=1,
        )
        db.add(question)
        db.flush()

    db.commit()

    context.memo["practice_email"] = email
    context.ids[f"node_{node_name}"] = str(node.id)
    context.ids[f"node_{node_name}_parent"] = str(parent.id)
    context.ids[f"question_{node_name}"] = str(question.id)
    context.memo[f"mastery_before_{node_name}"] = float(mastery.mastery_rate)
    context.memo[f"parent_mastery_before_{node_name}"] = float(parent_mastery.mastery_rate)
