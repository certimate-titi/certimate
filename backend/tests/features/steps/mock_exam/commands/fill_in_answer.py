"""When 使用者在填空欄輸入答案 — Command"""

import uuid

from behave import when


@when('使用者 "{email}" 在題目 {question_id:d} 的填空欄輸入 "{answer}"')
def step_impl(context, email, question_id, answer):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    exam_id = context.memo.get("current_exam_id")
    question_uuid = uuid.UUID(int=question_id)

    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/answers",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question_id": str(question_uuid),
            "selected_answer": answer,
        },
    )
    context.last_response = response
