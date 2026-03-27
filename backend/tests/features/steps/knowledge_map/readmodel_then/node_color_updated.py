"""Then 返回此頁面時，該節點的顏色應即時更新渲染為「綠色（熟練）」 — Aggregate Then"""

import uuid

from behave import then

from app.models.node_mastery import NodeMastery


@then('返回此頁面時，該節點的顏色應即時更新渲染為「綠色（熟練）」')
def node_color_updated(context):
    db = context.db_session
    target_node_id = context.memo.get("target_node_id")
    assert target_node_id, "target_node_id 未設定"

    mastery = (
        db.query(NodeMastery)
        .filter(NodeMastery.node_id == uuid.UUID(target_node_id))
        .first()
    )
    assert mastery is not None, (
        f"找不到 node_id={target_node_id} 的 NodeMastery 記錄"
    )

    # Refresh to get latest DB state
    db.refresh(mastery)

    assert mastery.color == "green", (
        f"預期節點顏色為 'green'，實際: '{mastery.color}'"
    )
