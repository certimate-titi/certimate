"""When 使用者查看群組的班級熱力圖 — Command (GET)"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 查看群組 (?P<group_id>\d+) 的班級熱力圖')
def step_impl(context, email, group_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    response = context.api_client.get(
        f"/api/v1/b2b/groups/{group_id}/heatmap",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
