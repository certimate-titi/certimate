"""When 使用者在頂部學科切換器選擇 "{subject_name}" — Query"""

from behave import when


@when('使用者在頂部學科切換器選擇 "{subject_name}"')
def switch_subject(context, subject_name):
    subject_key = f"subject_{subject_name}"
    if subject_key not in context.ids:
        raise KeyError(f"找不到學科 '{subject_name}' 的 ID（key: {subject_key}）")

    subject_id = context.ids[subject_key]
    token = context.memo["current_token"]

    response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{subject_id}/nodes",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
