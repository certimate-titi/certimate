"""Given 使用者提交測驗設定 — F19 交錯練習 Aggregate Given。

這些步驟作為 Given（前置狀態），內部直接建立 Exam 並將 exam_id 存入 context.memo。
"""

import uuid as uuid_mod

from behave import given

from app.models.exam import Exam, ExamStatus
from app.models.knowledge_node import KnowledgeNode
from app.models.resource import Resource


def _get_subject_id_from_nodes(db, nodes):
    """從節點清單取得 subject_id（優先 node.subject_id，次 resource.subject_id）。"""
    for n in nodes:
        if n.subject_id:
            return n.subject_id
        if n.resource_id:
            res = db.query(Resource).filter_by(id=n.resource_id).first()
            if res and res.subject_id:
                return res.subject_id
    return None


def _resolve_node_uuids(context, node_keys: list[int]) -> list[uuid_mod.UUID]:
    """從 context.ids 解析節點 UUID。"""
    result = []
    for k in node_keys:
        id_str = context.ids.get(f"node_{k}")
        assert id_str, f"找不到節點 {k} 的 ID（context.ids 無 node_{k}）"
        result.append(uuid_mod.UUID(id_str))
    return result


@given('使用者 "{email}" 提交測驗設定，選擇節點 1、2、3，題數為 9')
def step_submit_config_3nodes_9(context, email):
    """建立多節點（3）交錯練習測驗（9 題）。"""
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuids = [str(uuid_mod.UUID(int=k)) for k in [1, 2, 3]]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": node_uuids,
            "question_count": 9,
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


@given('使用者 "pro@example.com" 提交測驗設定，選擇節點 1，題數為 10')
def step_submit_config_single_node_10(context):
    """建立單節點測驗（10 題），應自動設為 sequential 模式。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuid = str(uuid_mod.UUID(int=1))

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": [node_uuid],
            "question_count": 10,
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


@given('使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2、3，題數為 10')
def step_submit_config_3nodes_10(context):
    """建立多節點（3）測驗（10 題）。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuids = [str(uuid_mod.UUID(int=k)) for k in [1, 2, 3]]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": node_uuids,
            "question_count": 10,
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


@given(
    '使用者 "pro@example.com" 提交測驗設定，選擇節點 1、2，'
    '題數為 10，難易度分配為 Easy:30% Medium:50% Hard:20%'
)
def step_submit_config_2nodes_difficulty(context):
    """建立多節點（2）交錯練習測驗（10 題，指定難度分配）。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    token = context.jwt_helper.generate_token(user_id)
    node_uuids = [str(uuid_mod.UUID(int=k)) for k in [1, 2]]

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "node_ids": node_uuids,
            "question_count": 10,
            "difficulty_distribution": {"easy": 30, "medium": 50, "hard": 20},
        },
    )
    context.last_response = response
    data = response.json()
    context.memo["current_exam_id"] = data.get("exam_id")
    context.memo["question_order_mode"] = data.get("question_order_mode")


@given('使用者 "pro@example.com" 的學習模式為 "sprint"')
def step_set_sprint_mode(context):
    """標記使用者學習模式為 sprint（存入 memo，供後續步驟使用）。"""
    context.memo["learning_mode"] = "sprint"


@given('使用者在節點 1 和節點 3 的歷史錯題較多')
def step_high_error_nodes(context):
    """標記高錯誤率節點（存入 memo，供 Sprint 模式排列使用）。"""
    context.memo["high_error_node_keys"] = [1, 3]


@given('使用者 "pro@example.com" 完成一場交錯練習模式的測驗')
def step_complete_interleaved_exam(context):
    """建立並完成一場交錯練習模式的測驗（狀態 SUBMITTED）。"""
    email = "pro@example.com"
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"

    db = context.db_session

    # 找節點
    node_uuid = uuid_mod.UUID(int=1)
    node = db.query(KnowledgeNode).filter_by(id=node_uuid).first()
    subject_id = None
    if node:
        subject_id = node.subject_id
        if not subject_id and node.resource_id:
            res = db.query(Resource).filter_by(id=node.resource_id).first()
            if res:
                subject_id = res.subject_id

    assert subject_id, "找不到節點的 subject_id，無法建立測驗"

    exam = Exam(
        user_id=uuid_mod.UUID(user_id),
        subject_id=subject_id,
        status=ExamStatus.SUBMITTED,
        total_questions=9,
        question_order_mode="interleaved",
        score=70,
        correct_count=6,
        passing_score=60,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    context.memo["current_exam_id"] = str(exam.id)
    context.memo["current_user_email"] = email
    context.memo["question_order_mode"] = "interleaved"
