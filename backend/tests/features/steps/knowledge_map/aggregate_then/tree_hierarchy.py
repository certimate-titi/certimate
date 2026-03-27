from behave import then
from app.models.knowledge_node import KnowledgeNode


@then('知識節點樹應包含至少兩層結構（主題 → 子概念）')
def step_impl(context):
    db = context.db_session
    resource_id = context.ids.get("last_resource_id")
    assert resource_id is not None, "找不到 last_resource_id"

    db.expire_all()
    nodes = db.query(KnowledgeNode).filter_by(resource_id=resource_id).all()
    max_depth = max((n.depth for n in nodes), default=-1)
    assert max_depth >= 1, \
        f"知識節點樹應至少有兩層結構（depth >= 1），實際最大深度為 {max_depth}"
