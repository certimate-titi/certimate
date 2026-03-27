"""When 使用者在知識心智圖頁面選擇科目 — Query"""

import uuid

from behave import when


@when('使用者 "{email}" 在知識心智圖頁面選擇科目 "{subject}"')
def step_impl(context, email, subject):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    if subject not in context.ids:
        raise KeyError(f"找不到科目 '{subject}' 的 ID")

    user_id = context.ids[email]
    subject_id = context.ids[subject]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/knowledge-map/subjects/{subject_id}/nodes",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
