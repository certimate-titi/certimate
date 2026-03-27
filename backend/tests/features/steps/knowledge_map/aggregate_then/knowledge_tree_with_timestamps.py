from behave import then
from app.models.knowledge_node import KnowledgeNode


@then('系統應自動為該影片建立知識節點樹（含時間軸標記）')
def step_impl(context):
    db = context.db_session
    resource_id = context.ids.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    db.expire_all()
    nodes = db.query(KnowledgeNode).filter_by(resource_id=resource_id).all()
    assert len(nodes) > 0, f"資源 {resource_id} 尚未建立任何知識節點"

    # 驗證至少有一個節點包含時間軸標記
    has_timestamp = any(n.source_timestamp_seconds is not None for n in nodes)
    assert has_timestamp, "影片知識節點樹應包含時間軸標記（source_timestamp_seconds）"
