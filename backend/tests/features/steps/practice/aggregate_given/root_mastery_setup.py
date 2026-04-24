"""Given 根節點掌握度 fixture — Epic 3 稀釋情境。"""

import uuid
from decimal import Decimal

from behave import given

from app.models.user import User
from app.models.subject import Subject
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery


@given('使用者 "{email}" 的根節點掌握度為 {rate:d}%')
def step_user_root_mastery(context, email, rate):
    """建立 root + 2 existing children，root 與兩子節點 mastery 皆為 rate%。"""
    db = context.db_session
    user = db.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    subject = db.query(Subject).first()
    if not subject:
        subject = Subject(name="AWS SAA")
        db.add(subject)
        db.flush()

    root = KnowledgeNode(
        subject_id=subject.id, name="考科根節點",
        depth=0, sort_order=0,
    )
    db.add(root)
    db.flush()

    existing_children = []
    for i in range(2):
        child = KnowledgeNode(
            subject_id=subject.id, parent_id=root.id,
            name=f"既有節點 {i+1}", depth=1, sort_order=i,
        )
        db.add(child)
        db.flush()
        existing_children.append(child)

        cm = NodeMastery(user_id=user.id, node_id=child.id)
        cm.mastery_rate = Decimal(str(rate))
        cm.correct_count = rate
        cm.total_count = 100
        db.add(cm)

    rm = NodeMastery(user_id=user.id, node_id=root.id)
    rm.mastery_rate = Decimal(str(rate))
    rm.correct_count = rate
    rm.total_count = 100
    db.add(rm)

    db.commit()

    context.memo["dilution_email"] = email
    context.ids["dilution_root"] = str(root.id)
    context.ids["dilution_subject"] = str(subject.id)
    context.memo["dilution_root_before"] = float(rm.mastery_rate)
    context.memo["dilution_existing_children"] = [str(c.id) for c in existing_children]
