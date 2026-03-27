"""Given 系統中有以下心智圖知識節點 — Aggregate Given"""

import uuid

from behave import given

from app.models.knowledge_node import KnowledgeNode
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository


@given('系統中有以下心智圖知識節點：')
def step_impl(context):
    db = context.db_session
    node_repo = KnowledgeNodeRepository(db)

    # 用 memo 記錄每個節點的可出題數（API 會用到）
    if "node_question_capacity" not in context.memo:
        context.memo["node_question_capacity"] = {}

    for row in context.table:
        node_id_int = int(row["節點 ID"])
        resource_id_int = int(row["資源 ID"])
        name = row["名稱"]
        question_capacity = int(row["可出題數"])

        node = KnowledgeNode(
            id=uuid.UUID(int=node_id_int),
            resource_id=uuid.UUID(int=resource_id_int),
            name=name,
            depth=1,
            sort_order=0,
            available_questions=question_capacity,
        )
        node_repo.save(node)

        context.ids[f"node_{node_id_int}"] = str(node.id)
        context.memo["node_question_capacity"][node_id_int] = question_capacity
