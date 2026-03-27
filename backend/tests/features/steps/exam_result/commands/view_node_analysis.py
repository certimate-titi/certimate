"""When 使用者查看測驗知識點分析 — Command (GET)"""

import uuid

from behave import when


@when('使用者 "{email}" 查看測驗 {exam_id:d} 的知識點分析')
def step_impl(context, email, exam_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    exam_uuid = uuid.UUID(int=exam_id)

    response = context.api_client.get(
        f"/api/v1/exams/{exam_uuid}/result/nodes",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
