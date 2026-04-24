"""Then 節點掌握度驗證 — Epic 3 Node Mastery Pipeline."""

import uuid

from behave import then

from app.models.node_mastery import NodeMastery


@then('節點 "{node_name}" 的掌握度應上升')
def step_node_mastery_increased(context, node_name):
    db = context.db_session
    node_id = context.ids.get(f"node_{node_name}")
    assert node_id, f"找不到節點 {node_name}"

    email = context.memo.get("practice_email")
    user_id = context.ids.get(email)

    db.expire_all()
    mastery = (
        db.query(NodeMastery)
        .filter(NodeMastery.user_id == uuid.UUID(user_id), NodeMastery.node_id == uuid.UUID(node_id))
        .first()
    )
    assert mastery, f"找不到節點 {node_name} 的 NodeMastery"

    before = context.memo.get(f"mastery_before_{node_name}", 0.0)
    after = float(mastery.mastery_rate)
    assert after > before, f"掌握度未上升：{before} → {after}"


@then('父節點的掌握度應連動更新（向上傳播）')
def step_parent_mastery_propagated(context):
    db = context.db_session

    email = context.memo.get("practice_email")
    user_id = context.ids.get(email)

    parent_id = None
    node_name = None
    for key, val in list(context.ids.items()):
        if key.endswith("_parent"):
            parent_id = val
            node_name = key[len("node_"):-len("_parent")]
            break
    assert parent_id, "找不到父節點"

    db.expire_all()
    parent_mastery = (
        db.query(NodeMastery)
        .filter(NodeMastery.user_id == uuid.UUID(user_id), NodeMastery.node_id == uuid.UUID(parent_id))
        .first()
    )
    assert parent_mastery, "父節點無 NodeMastery"

    before = context.memo.get(f"parent_mastery_before_{node_name}", 0.0)
    after = float(parent_mastery.mastery_rate)
    assert after != before, f"父節點掌握度未連動更新：{before} → {after}"
