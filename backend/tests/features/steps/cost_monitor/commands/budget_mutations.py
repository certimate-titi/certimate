"""When 預算修改/整體調整/解除停用 — Commands (PUT/POST)."""

from behave import when


def _auth_headers(context, email: str) -> dict:
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)
    return {"Authorization": f"Bearer {token}"}


@when('使用者 "{email}" 將 "{scope}" 月預算修改為 {amount:d} USD，原因為 "{reason}"')
def step_impl_update_with_reason(context, email, scope, amount, reason):
    context.last_response = context.api_client.put(
        "/api/v1/admin/cost/budget",
        json={
            "scope": scope,
            "monthly_limit_usd": amount,
            "reason": reason,
        },
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 將 "{scope}" 月預算修改為 {amount:d} USD')
def step_impl_update_no_reason(context, email, scope, amount):
    context.last_response = context.api_client.put(
        "/api/v1/admin/cost/budget",
        json={
            "scope": scope,
            "monthly_limit_usd": amount,
            "reason": "bdd default reason",
        },
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 執行整體調整 "+{pct:d}%"，原因為 "{reason}"')
def step_impl_global_scale_plus(context, email, pct, reason):
    factor = 1 + pct / 100
    context.last_response = context.api_client.post(
        "/api/v1/admin/cost/budget/global-scale",
        json={"scale_factor": factor, "reason": reason},
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 執行整體調整 "+{pct:d}%"')
def step_impl_global_scale_plus_no_reason(context, email, pct):
    factor = 1 + pct / 100
    context.last_response = context.api_client.post(
        "/api/v1/admin/cost/budget/global-scale",
        json={"scale_factor": factor, "reason": "bdd default"},
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 執行整體調整設為 {total:d} USD，原因為 "{reason}"')
def step_impl_global_set(context, email, total, reason):
    context.last_response = context.api_client.post(
        "/api/v1/admin/cost/budget/global-scale",
        json={"target_total_usd": total, "reason": reason},
        headers=_auth_headers(context, email),
    )


@when('使用者 "{email}" 手動解除停用 "{scope}"，原因為 "{reason}"')
def step_impl_override(context, email, scope, reason):
    context.last_response = context.api_client.post(
        "/api/v1/admin/cost/budget/override-disable",
        json={"scope": scope, "reason": reason},
        headers=_auth_headers(context, email),
    )
