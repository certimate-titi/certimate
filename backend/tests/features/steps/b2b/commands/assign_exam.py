"""When 使用者將考卷派發給群組 — Command (POST)"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 將考卷 (?P<exam_id>\d+) 派發給群組 (?P<group_id>\d+)，截止日期為 "(?P<deadline>[^"]+)"')
def step_impl(context, email, exam_id, group_id, deadline):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Get exam name from memo (stored by org_exam_config Given step)
    exam_config = context.memo.get(f"org_exam_{exam_id}", {})
    exam_name = exam_config.get("name", f"考卷 {exam_id}")

    response = context.api_client.post(
        f"/api/v1/b2b/groups/{group_id}/assign-exam",
        json={
            "exam_id": int(exam_id),
            "exam_name": exam_name,
            "deadline": deadline,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
