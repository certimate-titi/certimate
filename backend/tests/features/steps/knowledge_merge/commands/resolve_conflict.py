"""When 管理員解決合併衝突 — Command"""

from behave import when


@when('管理員 "{email}" 解決衝突，選擇 "{action}"')
def step_resolve_conflict(context, email, action):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    conflict_id = context.ids.get("conflict_1")
    assert conflict_id, "找不到衝突 ID"

    response = context.api_client.post(
        f"/api/v1/knowledge-merge/conflicts/{conflict_id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": action,
        },
    )
    context.last_response = response
