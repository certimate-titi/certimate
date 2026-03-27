"""When 使用者在 AI 教練視窗輸入 — Command (POST)"""

import uuid

from behave import when


@when('使用者 "{email}" 在測驗 {exam_id:d} 題目 {question_id:d} 的 AI 教練視窗輸入 "{message}"')
def step_impl(context, email, exam_id, question_id, message):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    exam_uuid = uuid.UUID(int=exam_id)
    q_uuid = uuid.UUID(int=question_id)

    response = context.api_client.post(
        f"/api/v1/wrong-answers/{exam_uuid}/questions/{q_uuid}/coach",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": message},
    )
    context.last_response = response
