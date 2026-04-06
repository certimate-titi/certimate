"""Then 合併後 mastery 數據不受影響 — Aggregate Then"""

from behave import then


@then('節點 "{name}" 的 mastery_rate 應維持 {rate:d}（不受合併影響）')
def step_mastery_preserved(context, name, rate):
    response = context.last_response
    data = response.json()

    # Check from API response
    nodes = data.get("nodes", data.get("tree", {}).get("nodes", []))
    for node in nodes:
        if node.get("name") == name:
            actual_rate = node.get("mastery_rate")
            if actual_rate is not None:
                assert int(float(actual_rate)) == rate, \
                    f"節點 '{name}' 的 mastery_rate 應維持 {rate}，實際為 {actual_rate}"
                return

    # Fallback: check from DB directly
    import uuid
    from app.models.node_mastery import NodeMastery

    db = context.db_session
    node_id = uuid.UUID(context.ids[f"node_{name}"])

    # Find the user from memo
    email = None
    for key in context.memo:
        if key.startswith(f"mastery_{name}_"):
            email = key.split("_", 2)[2]
            break

    if email:
        user_id = uuid.UUID(context.ids[email])
        mastery = db.query(NodeMastery).filter(
            NodeMastery.node_id == node_id,
            NodeMastery.user_id == user_id,
        ).first()

        assert mastery is not None, \
            f"找不到節點 '{name}' 的 mastery 紀錄"
        assert int(mastery.mastery_rate) == rate, \
            f"節點 '{name}' 的 mastery_rate 應維持 {rate}，實際為 {mastery.mastery_rate}"
