"""When 查詢待審退款清單 / 優惠碼清單 / 使用者申請退款 / 驗證優惠碼 — Commands"""

from behave import when


@when('使用者 "{email}" 查詢待審退款清單')
def step_list_refunds(context, email):
    token = context.jwt_helper.generate_token(context.ids[email])
    response = context.api_client.get(
        "/api/v1/admin/finance/refunds?status=pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢優惠碼清單')
def step_list_coupons(context, email):
    token = context.jwt_helper.generate_token(context.ids[email])
    response = context.api_client.get(
        "/api/v1/admin/finance/coupons",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 對交易 "{txn_id}" 申請退款，金額為 {amount:d}，理由為 "{reason}"')
def step_request_refund(context, email, txn_id, amount, reason):
    token = context.jwt_helper.generate_token(context.ids[email])
    response = context.api_client.post(
        "/api/v1/subscriptions/refund-request",
        headers={"Authorization": f"Bearer {token}"},
        json={"transaction_id": txn_id, "amount": amount, "reason": reason},
    )
    context.last_response = response


@when('使用者 "{email}" 驗證優惠碼 "{code}"，方案為 "{plan}"，金額為 {amount:d}')
def step_validate_coupon(context, email, code, plan, amount):
    token = context.jwt_helper.generate_token(context.ids[email])
    response = context.api_client.post(
        "/api/v1/subscriptions/coupons/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": code, "plan": plan, "amount": amount},
    )
    context.last_response = response
