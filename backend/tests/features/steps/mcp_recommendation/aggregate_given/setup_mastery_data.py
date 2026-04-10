"""
設置用戶掌握度數據和知識樹結構
"""

from behave import given
import uuid
from datetime import datetime, timezone
from app.models.knowledge_node import KnowledgeNode
from app.models.node_mastery import NodeMastery
from app.models.subject import Subject


@given('用戶 "{email}" 在該知識節點上掌握度為 {mastery:f}')
def step_set_node_mastery(context, email, mastery):
    """設置用戶在知識節點上的掌握度"""
    user_id = context.ids.get(email)
    if not user_id:
        raise ValueError(f"User {email} not found")

    # 獲取最後創建的節點
    if "knowledge_nodes" not in context.memo:
        raise ValueError("No knowledge nodes found")

    last_topic = list(context.memo["knowledge_nodes"].keys())[-1]
    node_id = uuid.UUID(context.memo["knowledge_nodes"][last_topic])

    # 創建或更新 NodeMastery 記錄
    nm = context.db_session.query(NodeMastery).filter(
        NodeMastery.user_id == uuid.UUID(user_id),
        NodeMastery.node_id == node_id
    ).first()

    if nm:
        nm.base_mastery = mastery
    else:
        nm = NodeMastery(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            node_id=node_id,
            base_mastery=mastery
        )
        context.db_session.add(nm)

    context.db_session.commit()


@given('用戶 "{email}" 在 {days:d} 天前答對題目 "{question_id}"')
def step_create_correct_answer(context, email, days, question_id):
    """創建正確答題記錄"""
    user_id = context.ids.get(email)
    if not user_id:
        raise ValueError(f"User {email} not found")

    # 如果 question_id 在 memo 中，使用實際的 ID
    actual_question_id = context.memo.get(f"question_{question_id}", question_id)

    question = context.db_session.query(Question).filter_by(id=uuid.UUID(actual_question_id)).first()
    if not question:
        raise ValueError(f"Question {actual_question_id} not found")

    answer = Answer(
        id=uuid.uuid4(),
        exam_id=question.exam_id,
        question_id=question.id,
        user_id=uuid.UUID(user_id),
        selected_answer="A",
        is_correct=True,
        created_at=datetime.now(timezone.utc)
    )
    context.db_session.add(answer)
    context.db_session.commit()

    # 記錄題目 ID
    context.memo[f"question_{question_id}"] = str(question.id)


@given('知識節點樹狀結構：')
def step_create_node_hierarchy(context):
    """根據表格創建知識節點樹"""
    # 獲取或創建 subject
    subject = context.db_session.query(Subject).filter_by(name="General").first()
    if not subject:
        subject = Subject(
            id=uuid.uuid4(),
            name="General",
            code="GEN"
        )
        context.db_session.add(subject)
        context.db_session.commit()

    nodes = {}

    for row in context.table:
        parent_name = row["父節點"]
        child_name = row["子節點"]

        # 創建或獲取父節點
        if parent_name not in nodes:
            parent = context.db_session.query(KnowledgeNode).filter_by(name=parent_name).first()
            if not parent:
                parent = KnowledgeNode(
                    id=uuid.uuid4(),
                    name=parent_name,
                    subject_id=subject.id,
                    depth=0
                )
                context.db_session.add(parent)
                context.db_session.commit()
            nodes[parent_name] = parent.id

        # 創建子節點
        if child_name not in nodes:
            child = KnowledgeNode(
                id=uuid.uuid4(),
                name=child_name,
                subject_id=subject.id,
                parent_id=nodes[parent_name],
                depth=1
            )
            context.db_session.add(child)
            context.db_session.commit()
            nodes[child_name] = child.id

    context.db_session.commit()
    context.memo["node_hierarchy"] = nodes


@given('知識節點資料：')
def step_set_node_data(context):
    """設置知識節點的詳細數據"""
    import json

    # 假設整個表格作為 JSON 字符串解析
    data_str = context.text
    node_data = json.loads(data_str)

    context.memo["node_data"] = node_data


@given('知識節點資料不含 definition 字段')
def step_set_incomplete_node_data(context):
    """設置不完整的知識節點數據"""
    node_data = {
        "name": "Incomplete Node",
        "examples": ["Example 1"],
        "relationships": []
    }
    context.memo["node_data"] = node_data
