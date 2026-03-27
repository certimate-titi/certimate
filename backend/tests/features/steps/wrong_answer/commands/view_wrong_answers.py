"""When 使用者查看錯題記錄 / 解析 — Command (GET)"""

import uuid

from behave import when


@when('使用者 "{email}" 查看測驗 {exam_id:d} 的錯題記錄')
def step_impl(context, email, exam_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    exam_uuid = uuid.UUID(int=exam_id)

    response = context.api_client.get(
        f"/api/v1/wrong-answers/{exam_uuid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查看測驗 {exam_id:d} 題目 {question_id:d} 的解析')
def step_impl_analysis(context, email, exam_id, question_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    exam_uuid = uuid.UUID(int=exam_id)
    q_uuid = uuid.UUID(int=question_id)

    response = context.api_client.get(
        f"/api/v1/wrong-answers/{exam_uuid}/questions/{q_uuid}/analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
