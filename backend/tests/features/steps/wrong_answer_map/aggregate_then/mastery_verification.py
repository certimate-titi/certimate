"""Then 節點掌握度驗證 — Aggregate Then"""

import uuid

from behave import then

from app.models.node_mastery import NodeMastery


@then('節點 "{node_name}" 的 mastery_rate 應為 {rate:d}')
def step_impl_rate(context, node_name, rate):
    db = context.db_session
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    # Find most recent user from context
    user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            user_id = uuid.UUID(val)
            break

    mastery = db.query(NodeMastery).filter_by(
        user_id=user_id, node_id=node_id
    ).first()

    assert mastery is not None, f"找不到節點 '{node_name}' 的掌握度記錄"
    assert int(mastery.mastery_rate) == rate, \
        f"期望 mastery_rate={rate}, 實際={mastery.mastery_rate}"


@then('節點 "{node_name}" 的 color 應為 "{expected_color}"')
def step_impl_color(context, node_name, expected_color):
    db = context.db_session
    node_id = uuid.UUID(context.ids[f"node_{node_name}"])

    user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            user_id = uuid.UUID(val)
            break

    mastery = db.query(NodeMastery).filter_by(
        user_id=user_id, node_id=node_id
    ).first()

    assert mastery is not None, f"找不到節點 '{node_name}' 的掌握度記錄"
    assert mastery.color == expected_color, \
        f"期望 color={expected_color}, 實際={mastery.color}"
