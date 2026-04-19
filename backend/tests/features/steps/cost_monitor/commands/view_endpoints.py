"""When 使用者查看成本監控各頁 — Commands (GET)."""

from behave import when


def _auth_headers(context, email: str) -> dict:
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)
    return {"Authorization": f"Bearer {token}"}


@when('使用者 "{email}" 查看成本監控總覽')
def step_impl_summary(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/admin/cost/summary",
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 查看供應商 "{provider}" 用量詳情')
def step_impl_provider(context, email, provider):
    context.last_response = context.api_client.get(
        f"/api/v1/admin/cost/providers/{provider}",
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 查看 GCP 服務分類')
def step_impl_gcp_services(context, email):
    context.last_response = context.api_client.get(
        "/api/v1/admin/cost/gcp/services",
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 查看成本趨勢圖，範圍為最近 {days:d} 天')
def step_impl_trends(context, email, days):
    context.last_response = context.api_client.get(
        f"/api/v1/admin/cost/trends?days={days}",
        headers=_auth_headers(context, email),
    )
