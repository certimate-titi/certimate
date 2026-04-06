"""When 使用者查看學員補考預設比例 — Command (GET)"""
from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 查看學員 (?P<student_id>\d+) 的補考預設比例')
def step_view_remediation_defaults(context, email, student_id):
    """GET /api/v1/b2b/students/{student_id}/remediation-defaults"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    actual_student_id = context.ids.get(str(student_id), str(student_id))
    context.last_response = context.api_client.get(
        f"/api/v1/b2b/students/{actual_student_id}/remediation-defaults",
        headers={"Authorization": f"Bearer {token}"},
    )


use_step_matcher("parse")
