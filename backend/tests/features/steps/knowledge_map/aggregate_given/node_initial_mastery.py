"""Given 某心智圖知識節點初始狀態為「紅色（不熟練，答對率 0%）」 — Aggregate Given"""

import uuid

from behave import given

from app.models.node_mastery import NodeMastery


@given('某心智圖知識節點初始狀態為「紅色（不熟練，答對率 0%）」')
def node_initial_mastery(context):
    db = context.db_session

    # Pick a node from context.ids (use the first available node)
    node_id = None
    for key in context.ids:
        if key.startswith("node_") and key != "node_root":
            node_id = uuid.UUID(context.ids[key])
            break
    if not node_id:
        raise KeyError("需要至少一個知識節點")

    # Pick first user
    user_id = None
    for key in context.ids:
        if "@" in key:
            user_id = uuid.UUID(context.ids[key])
            break
    if not user_id:
        raise KeyError("需要至少一個使用者")

    # Generate JWT token for this user
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_user_id"] = str(user_id)

    # Create NodeMastery record with red color and 0% mastery
    mastery = NodeMastery(
        user_id=user_id,
        node_id=node_id,
        correct_count=0,
        total_count=0,
        mastery_rate=0,
        color="red",
    )
    db.add(mastery)
    db.commit()

    context.memo["target_node_id"] = str(node_id)
