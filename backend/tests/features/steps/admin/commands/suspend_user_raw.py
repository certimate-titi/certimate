"""When 使用者停權使用者帳號（原始參數，含缺少參數測試） — Command (POST)"""

import re
from behave import step


def _do_suspend(context, email, user_id_key, reason):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    body = {}
    uid = user_id_key.strip() if user_id_key else ""
    rsn = reason.strip() if reason else ""

    if uid:
        resolved = context.ids.get(uid)
        body["target_user_id"] = resolved
    if rsn:
        body["reason"] = rsn

    response = context.api_client.post(
        "/api/v1/admin/users/suspend",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


# Case: missing user_id (empty), reason provided
@step('使用者 "{email}" 停權使用者帳號，使用者 ID 為 ，原因為 {reason}')
def step_suspend_missing_user_id(context, email, reason):
    _do_suspend(context, email, "", reason)


# Case: user_id provided, missing reason (empty)
@step('使用者 "{email}" 停權使用者帳號，使用者 ID 為 {user_id_key}，原因為 ')
def step_suspend_missing_reason(context, email, user_id_key):
    _do_suspend(context, email, user_id_key, "")
