from behave import then
from app.models.knowledge_node import KnowledgeNode
from app.repositories.knowledge_node_repository import KnowledgeNodeRepository


@then('每個葉節點應關聯原文溯源位置（PDF 頁碼或 YouTube 時間戳）')
def step_impl(context):
    db = context.db_session
    resource_id = context.ids.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    db.expire_all()
    repo = KnowledgeNodeRepository(db)
    leaves = repo.find_leaves_by_resource_id(resource_id)
    assert len(leaves) > 0, "找不到任何葉節點"

    for leaf in leaves:
        has_source = (
            leaf.source_page_number is not None
            or leaf.source_timestamp_seconds is not None
        )
        assert has_source, \
            f"葉節點 '{leaf.name}' 缺少原文溯源位置（source_page_number 或 source_timestamp_seconds）"
