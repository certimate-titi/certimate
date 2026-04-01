"""When 系統執行異常偵測排程 — Command (GET)"""

from behave import when


@when('系統執行異常偵測排程')
def step_impl(context):
    # Use a super_admin token if available, otherwise use the first admin-like user
    admin_email = "super@certimate.com"
    user_id = context.ids.get(admin_email)
    if user_id is None:
        # Fallback: find any admin in context.ids
        for key, val in context.ids.items():
            if "super" in key or "admin" in key:
                user_id = val
                break

    headers = {}
    if user_id:
        token = context.jwt_helper.generate_token(user_id)
        headers["Authorization"] = f"Bearer {token}"

    # Pass worker failure rate from context.memo if available
    params = {}
    if hasattr(context, "memo") and "worker_failure_rate" in context.memo:
        params["worker_failure_rate"] = context.memo["worker_failure_rate"]

    response = context.api_client.get(
        "/api/v1/admin/dashboard/alerts",
        params=params,
        headers=headers,
    )
    context.last_response = response
