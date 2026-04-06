"""When 使用者批量移除學生 — Command (POST)"""
from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 批量移除機構 (?P<inst_id>\d+) 的以下學生：')
def step_batch_remove_students(context, email, inst_id):
    """POST /api/v1/b2b/students/batch-remove"""
    student_emails = [row["Email"] for row in context.table]
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.last_response = context.api_client.post(
        "/api/v1/b2b/students/batch-remove",
        json={"emails": student_emails},
        headers={"Authorization": f"Bearer {token}"},
    )


use_step_matcher("parse")
