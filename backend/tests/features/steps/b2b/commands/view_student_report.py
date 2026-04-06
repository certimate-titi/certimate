"""When 使用者查看學員詳情報告 — Command (GET)"""
import uuid as _uuid

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 查看學員 (?P<student_id>\d+) 的詳情報告')
def step_view_student_report(context, email, student_id):
    """GET /api/v1/b2b/students/{student_id}/report"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    # Resolve student_id; for unknown IDs generate a deterministic UUID
    actual_student_id = context.ids.get(
        str(student_id), str(_uuid.UUID(int=int(student_id)))
    )
    context.last_response = context.api_client.get(
        f"/api/v1/b2b/students/{actual_student_id}/report",
        headers={"Authorization": f"Bearer {token}"},
    )


use_step_matcher("parse")
