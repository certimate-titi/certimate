"""When 使用者為群組生成弱點針對練習卷 — Command (POST)"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 為群組 (?P<group_id>\d+) 生成弱點針對練習卷，題數為 (?P<count>\d+)')
def step_impl(context, email, group_id, count):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.post(
        f"/api/v1/b2b/exam/remediation/{group_id}",
        json={"question_count": int(count)},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
