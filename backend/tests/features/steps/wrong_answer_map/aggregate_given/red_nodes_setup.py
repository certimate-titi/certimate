"""Given 使用者 "{email}" 的錯題地圖中有 {count:d} 個紅色節點."""

import uuid
from decimal import Decimal
from behave import given
from app.models.user import User
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.subject import Subject
from app.models.learning_journey import LearningJourney


@given('使用者 "{email}" 的錯題地圖中有 {count:d} 個紅色節點')
def step_impl(context, email, count):
    """建立指定數量的紅色節點（mastery_rate < 60%）給使用者。"""
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    # 確保有考科
    subject = context.db_session.query(Subject).first()
    if not subject:
        subject = Subject(id=uuid.uuid4(), name="信託業業務人員", category_id=None)
        context.db_session.add(subject)
        context.db_session.flush()

    # 確保有學習歷程
    journey = context.db_session.query(LearningJourney).filter(
        LearningJourney.user_id == user.id,
        LearningJourney.subject_id == subject.id,
    ).first()
    if not journey:
        journey = LearningJourney(
            id=uuid.uuid4(),
            user_id=user.id,
            subject_id=subject.id,
        )
        context.db_session.add(journey)
        context.db_session.flush()

    # 建立 count 個紅色節點（mastery_rate < 60%）
    red_node_ids = []
    for i in range(count):
        node = KnowledgeNode(
            id=uuid.uuid4(),
            subject_id=subject.id,
            name=f"弱點節點_{i}",
            depth=2,
        )
        context.db_session.add(node)
        context.db_session.flush()

        # 答對率設為 30% — 紅色節點
        mastery_rate = Decimal("30.00")
        mastery = NodeMastery(
            id=uuid.uuid4(),
            user_id=user.id,
            node_id=node.id,
            correct_count=3,
            total_count=10,
            mastery_rate=mastery_rate,
            color="red",
        )
        context.db_session.add(mastery)
        red_node_ids.append(str(node.id))

    context.db_session.commit()
    context.memo["red_node_ids"] = red_node_ids
    context.memo["subject_id"] = str(subject.id)
    context.memo["ai_suggestion_email"] = email
