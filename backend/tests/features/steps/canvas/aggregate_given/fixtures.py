"""Canvas BDD — Aggregate Given fixtures (PRD-046).

Covers:
- 使用者 "X" 備考 "Y"
- 科目 "X" 下有三層知識樹：
- 使用者 "X" 對節點 N 的 mastery_rate 為 V
- 另有科目 N 下節點 M
- 科目 N 下所有節點被刪除
"""

import uuid
from datetime import date

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.models.learning_journey import LearningJourney
from app.models.node_mastery import NodeMastery
from app.models.subject import Subject, SubjectCategory


def _node_uuid(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


def _subject_uuid(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


@given('使用者 "{email}" 備考 "{subject_name}"')
def step_user_prepare_subject(context, email, subject_name):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    subject_id = uuid.UUID(context.ids[subject_name])

    journey = LearningJourney(
        user_id=user_id,
        subject_id=subject_id,
        exam_date=date.today(),
    )
    db.add(journey)
    db.commit()


@given('科目 "{subject_name}" 下有三層知識樹：')
def step_knowledge_tree(context, subject_name):
    db = context.db_session
    subject_id = uuid.UUID(context.ids[subject_name])

    for row in context.table:
        node_id = _node_uuid(int(row["節點 ID"]))
        name = row["名稱"]
        depth = int(row["depth"])
        parent_raw = row["父節點"].strip()
        parent_id = None if parent_raw in ("null", "") else _node_uuid(int(parent_raw))

        node = KnowledgeNode(
            id=node_id,
            subject_id=subject_id,
            parent_id=parent_id,
            name=name,
            depth=depth,
            sort_order=0,
        )
        db.add(node)
        context.ids[f"canvas_node_{name}"] = str(node_id)
    db.commit()


@given('使用者 "{email}" 對節點 {node_num:d} 的 mastery_rate 為 {rate:d}')
def step_node_mastery(context, email, node_num, rate):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    node_id = _node_uuid(node_num)

    mastery = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        correct_count=rate,
        total_count=100,
        mastery_rate=rate,
        color="green" if rate >= 70 else ("yellow" if rate >= 40 else "red"),
    )
    db.add(mastery)
    db.commit()


@given('另有科目 {subject_num:d} 下節點 {node_num:d}')
def step_extra_subject_node(context, subject_num, node_num):
    db = context.db_session
    category = db.query(SubjectCategory).first()
    if not category:
        category = SubjectCategory(name="預設分類", sort_order=0)
        db.add(category)
        db.flush()

    subject_id = _subject_uuid(subject_num)
    subject = Subject(id=subject_id, category_id=category.id, name=f"OtherSubject{subject_num}")
    db.add(subject)
    db.commit()

    node = KnowledgeNode(
        id=_node_uuid(node_num),
        subject_id=subject_id,
        parent_id=None,
        name=f"OtherNode{node_num}",
        depth=0,
        sort_order=0,
    )
    db.add(node)
    db.commit()


@given('科目 {subject_num:d} 下所有節點被刪除')
def step_delete_all_nodes(context, subject_num):
    db = context.db_session
    subject_id = _subject_uuid(subject_num)
    # 先刪 mastery（FK 依賴）
    node_ids = [
        n.id for n in
        db.query(KnowledgeNode).filter_by(subject_id=subject_id).all()
    ]
    if node_ids:
        db.query(NodeMastery).filter(NodeMastery.node_id.in_(node_ids)).delete(synchronize_session=False)
        db.query(KnowledgeNode).filter(KnowledgeNode.subject_id == subject_id).delete(synchronize_session=False)
    db.commit()
