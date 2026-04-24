"""When 使用者在頂部學科切換器選擇 "{subject_name}" — Query"""

from behave import when


@when('使用者在頂部學科切換器選擇 "{subject_name}"')
def switch_subject(context, subject_name):
    subject_key = f"subject_{subject_name}"
    if subject_key not in context.ids:
        raise KeyError(f"找不到學科 '{subject_name}' 的 ID（key: {subject_key}）")

    subject_id = context.ids[subject_key]
    token = context.memo["current_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 前端切換學科時並行發兩個請求：資源列表 + 節點樹
    resources_response = context.api_client.get(
        f"/api/v1/resources?subject_id={subject_id}",
        headers=headers,
    )
    nodes_response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{subject_id}/nodes",
        headers=headers,
    )
    context.memo["resources_response"] = resources_response
    context.memo["nodes_response"] = nodes_response
    context.last_response = nodes_response  # 預設 last_response 為 nodes（向下相容）
