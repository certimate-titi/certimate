"""When 使用者繼續進行測驗 — Command (GET)"""

import uuid

from behave import when


@when('使用者 "{email}" 繼續進行測驗 {exam_id:d}')
def step_impl(context, email, exam_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    exam_uuid = uuid.UUID(int=exam_id)

    response = context.api_client.get(
        f"/api/v1/exams/{exam_uuid}/resume",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
