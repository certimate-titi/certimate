"""When 使用者在會員中心移除備考科目 — Command (DELETE)"""

from behave import when


@when('使用者在會員中心移除備考科目 "{subject}"')
def step_impl(context, subject):
    email = context.memo.get("current_email")
    if not email:
        for key in context.ids:
            if "@" in key:
                email = key
                break
    user_id = context.ids.get(email)
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email

    subject_id = context.ids.get(f"subject_{subject}", subject)
    context.memo["pending_remove_subject_id"] = subject_id

    response = context.api_client.delete(
        f"/api/v1/subjects/{subject_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
