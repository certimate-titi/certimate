"""Then 各節點顏色驗證 — ReadModel Then"""

from behave import then


@then('各節點顏色應為：')
def step_impl(context):
    # This is a verification step that checks color rules
    # The actual data is set in Given steps via NodeMastery records
    # We verify by querying the DB directly
    import uuid
    from app.models.node_mastery import NodeMastery

    db = context.db_session

    user_id = None
    for key, val in context.ids.items():
        if "@" in key:
            user_id = uuid.UUID(val)
            break

    for row in context.table:
        node_name = row["節點名稱"]
        expected_color = row["預期顏色"]

        node_id = uuid.UUID(context.ids[f"node_{node_name}"])
        mastery = db.query(NodeMastery).filter_by(
            user_id=user_id, node_id=node_id
        ).first()

        assert mastery is not None, f"找不到節點 '{node_name}' 的掌握度"
        assert mastery.color == expected_color, \
            f"節點 '{node_name}' 期望顏色={expected_color}, 實際={mastery.color}"
