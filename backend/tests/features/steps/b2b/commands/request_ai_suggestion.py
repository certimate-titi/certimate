"""When 使用者為學員請求 AI 補強建議 — Command (POST)"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 為學員 (?P<student_id>\d+) 請求 AI 補強建議')
def step_impl(context, email, student_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Resolve student_id to actual UUID
    actual_student_id = context.ids.get(student_id, student_id)

    response = context.api_client.post(
        f"/api/v1/b2b/students/{actual_student_id}/ai-suggestions",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
