"""When 使用者點擊頁尾的「意見反饋」連結 — Command (GET)"""

from behave import when


@when('使用者點擊頁尾的「意見反饋」連結')
def step_impl(context):
    logged_in_email = context.memo.get("logged_in_email")
    not_logged_in = context.memo.get("not_logged_in", False)

    if not_logged_in or not logged_in_email:
        # Unauthenticated: call without auth header
        response = context.api_client.get("/api/v1/feedback")
        context.last_response = response
        # Store redirect info for Then steps
        context.memo["redirect_target"] = "/login"
        context.memo["redirect_after_login"] = "/feedback"
    else:
        user_id = context.ids[logged_in_email]
        token = context.jwt_helper.generate_token(user_id)
        response = context.api_client.get(
            "/api/v1/feedback",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
        context.memo["redirect_target"] = "/feedback"
