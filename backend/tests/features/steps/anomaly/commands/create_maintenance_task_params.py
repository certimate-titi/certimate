"""When 使用者建立維修任務（帶參數） — Command"""

from behave import when, use_step_matcher

use_step_matcher("re")


@when('使用者 "(?P<email>[^"]+)" 建立維修任務，名稱為 (?P<name>.*)，優先級為 (?P<priority>.*)')
def step_impl(context, email, name, priority):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    body = {}
    name = name.strip()
    priority = priority.strip()
    if name:
        body["name"] = name
    if priority:
        body["priority"] = priority

    response = context.api_client.post(
        "/api/v1/admin/maintenance-tasks",
        headers={"Authorization": f"Bearer {token}"},
        json=body,
    )
    context.last_response = response


use_step_matcher("parse")
