"""Then 根節點掌握度稀釋驗證 — Epic 3。"""

import uuid

from behave import then

from app.models.node_mastery import NodeMastery


@then('根節點掌握度應因分母變大而下降')
def step_root_mastery_decreased(context):
    db = context.db_session
    root_id = context.ids["dilution_root"]
    email = context.memo["dilution_email"]
    user_id = context.ids[email]

    db.expire_all()
    mastery = (
        db.query(NodeMastery)
        .filter(
            NodeMastery.user_id == uuid.UUID(user_id),
            NodeMastery.node_id == uuid.UUID(root_id),
        )
        .first()
    )
    assert mastery, "找不到根節點 NodeMastery"

    before = context.memo["dilution_root_before"]
    after = float(mastery.mastery_rate)
    assert after < before, f"掌握度未下降：{before} → {after}"
