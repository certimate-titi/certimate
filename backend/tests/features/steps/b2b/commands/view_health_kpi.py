"""When 使用者查看機構的班級健康摘要 — Command (GET)"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 查看機構 (?P<inst_id>\d+) 的班級健康摘要')
def step_impl(context, email, inst_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/b2b/institutions/{inst_id}/health-kpi",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
