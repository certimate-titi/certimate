"""When 使用者提交測驗設定（含 table）— Command"""

import json
import uuid

from behave import when, use_step_matcher

use_step_matcher("re")


@when('使用者 "(?P<email>[^"]+)" 提交測驗設定：')
def step_impl(context, email):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Parse table into config dict
    config = {}
    for row in context.table:
        config[row["欄位"]] = row["值"]

    # Parse node_ids — could be names like [人工智慧基礎概論, 生成式AI應用與規劃]
    node_ids_raw = config.get("node_ids", "[]")
    # Remove brackets
    node_ids_raw = node_ids_raw.strip("[]")
    node_names = [n.strip() for n in node_ids_raw.split(",") if n.strip()]

    node_uuids = []
    for name in node_names:
        key = f"node_{name}"
        if key in context.ids:
            node_uuids.append(context.ids[key])
        else:
            # Try finding in DB by name
            from app.models.knowledge_node import KnowledgeNode
            node = context.db_session.query(KnowledgeNode).filter(
                KnowledgeNode.name == name
            ).first()
            if node:
                node_uuids.append(str(node.id))
            else:
                try:
                    node_uuids.append(str(uuid.UUID(int=int(name))))
                except (ValueError, TypeError):
                    node_uuids.append(str(uuid.uuid5(uuid.NAMESPACE_DNS, name)))

    # If no valid nodes found by name, fall back to subject's nodes
    if not node_uuids or all(_is_synthetic(u, node_names) for u in node_uuids):
        subject_key = context.memo.get(f"current_subject_{email}")
        if subject_key:
            from app.models.knowledge_node import KnowledgeNode
            from app.models.resource import Resource
            import uuid as _uuid
            subject_nodes = context.db_session.query(KnowledgeNode).join(
                Resource, KnowledgeNode.resource_id == Resource.id
            ).filter(Resource.subject_id == _uuid.UUID(subject_key)).all()
            if subject_nodes:
                node_uuids = [str(n.id) for n in subject_nodes]

    question_count = int(config.get("question_count", "10"))
    exam_mode = config.get("exam_mode", "mixed")

    payload = {
        "node_ids": node_uuids,
        "question_count": question_count,
        "exam_mode": exam_mode,
    }

    response = context.api_client.post(
        "/api/v1/exams/config",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response


def _is_synthetic(uid: str, names: list[str]) -> bool:
    """Check if a UUID was synthetically generated (not from DB)."""
    for name in names:
        try:
            if uid == str(uuid.UUID(int=int(name))):
                return True
        except (ValueError, TypeError):
            pass
        if uid == str(uuid.uuid5(uuid.NAMESPACE_DNS, name)):
            return True
    return False


use_step_matcher("parse")
