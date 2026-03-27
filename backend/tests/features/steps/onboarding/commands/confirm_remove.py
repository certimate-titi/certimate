"""When 使用者確認移除 — Command (POST)"""

from behave import when


@when('使用者確認移除')
def step_impl(context):
    token = context.memo.get("current_token")
    subject_id = context.memo.get("pending_remove_subject_id")

    response = context.api_client.post(
        f"/api/v1/subjects/{subject_id}/confirm-remove",
        headers={"Authorization": f"Bearer {token}"},
        json={"confirmed": True},
    )
    context.last_response = response
