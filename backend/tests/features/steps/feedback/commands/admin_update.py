"""When 使用者 "..." 更新反饋 "..."：(with table / inline) — Command (PUT)"""

from behave import when, use_step_matcher

FIELD_MAP = {
    "狀態": "status",
    "管理員回覆": "admin_reply",
    "原因": "close_reason",
}


@when('使用者 "{email}" 更新反饋 "{feedback_id}"：')
def step_impl_table(context, email, feedback_id):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {}
    for row in context.table:
        field_name = row["欄位"]
        field_key = FIELD_MAP.get(field_name, field_name)
        payload[field_key] = row["值"]

    response = context.api_client.put(
        f"/api/v1/feedback/admin/{feedback_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response


use_step_matcher("re")


@when('使用者 "(?P<email>[^"]+)" 更新反饋 "(?P<feedback_id>[^"]+)"，狀態為 "(?P<status>[^"]+)"(?:，原因為 "(?P<reason>[^"]+)")?')
def step_impl_inline(context, email, feedback_id, status, reason=None):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    payload = {"status": status}
    if reason:
        payload["close_reason"] = reason

    response = context.api_client.put(
        f"/api/v1/feedback/admin/{feedback_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    context.last_response = response


use_step_matcher("parse")
