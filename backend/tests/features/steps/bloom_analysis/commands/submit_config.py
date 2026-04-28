"""When 提交測驗設定 — Bloom 出題情境。"""

import uuid
from behave import when

from app.models.subject import Subject
from app.models.knowledge_node import KnowledgeNode


def _login_user(context, email: str) -> str:
    user_id = context.ids.get(email)
    assert user_id, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(user_id)
    return token


def _resolve_node_id(context, subject_name: str) -> str:
    db = context.db_session
    subj = db.query(Subject).filter_by(name=subject_name).first()
    assert subj, f"找不到學科 {subject_name}"
    node = db.query(KnowledgeNode).filter_by(subject_id=subj.id).first()
    assert node, f"學科 {subject_name} 無知識節點，請確認前置步驟"
    return str(node.id)


@when('使用者 "{email}" 提交測驗設定，選擇學科 "{subject_name}"，題數為 {count:d}')
def step_submit_default(context, email, subject_name, count):
    token = _login_user(context, email)
    node_id = _resolve_node_id(context, subject_name)
    response = context.api_client.post(
        "/api/v1/exams/config",
        json={"node_ids": [node_id], "question_count": count},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["last_subject_name"] = subject_name


@when('使用者 "{email}" 提交測驗設定，選擇學科 "{subject_name}"，題數為 {count:d}，並手動指定 Bloom 配比為：')
def step_submit_with_custom_bloom(context, email, subject_name, count):
    token = _login_user(context, email)
    node_id = _resolve_node_id(context, subject_name)
    custom_bloom = {row["bloom_category"]: int(row["custom_percentage"]) for row in context.table}
    response = context.api_client.post(
        "/api/v1/exams/config",
        json={
            "node_ids": [node_id],
            "question_count": count,
            "custom_bloom_ratio": custom_bloom,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["submitted_bloom_distribution"] = custom_bloom
    context.memo["last_subject_name"] = subject_name
