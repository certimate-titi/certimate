"""When 使用者處理某檢舉 — Command (POST)"""

from behave import when


@when('使用者 "{email}" 處理檢舉 "{report_ref}"，動作為 "{action}"，備註為 "{note}"')
def step_impl(context, email, report_ref, action, note):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    response = context.api_client.post(
        f"/api/v1/admin/moderation/reports/{report_ref}/resolve",
        json={"action": action, "note": note},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
