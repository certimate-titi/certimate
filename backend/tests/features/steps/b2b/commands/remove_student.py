"""When 使用者移除單一學生 — Command (DELETE)"""
import uuid as _uuid

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 移除機構 (?P<inst_id>\d+) 的學生 "(?P<student_email>[^"]+)"')
def step_remove_student(context, email, inst_id, student_email):
    """DELETE /api/v1/b2b/institutions/{inst_id}/students/{student_email}"""
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    actual_inst_id = context.ids.get(
        f"institution_{inst_id}", str(_uuid.UUID(int=int(inst_id)))
    )
    context.last_response = context.api_client.delete(
        f"/api/v1/b2b/institutions/{actual_inst_id}/students/{student_email}",
        headers={"Authorization": f"Bearer {token}"},
    )


use_step_matcher("parse")
