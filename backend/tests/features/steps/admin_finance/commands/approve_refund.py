"""When 使用者核准退款（支援可選 OTP 參數）— Command (POST)"""

from behave import step, use_step_matcher

use_step_matcher("re")


@step(r'使用者 "(?P<email>[^"]+)" 核准退款 "(?P<refund_id>[^"]+)"(?:，OTP 為 "(?P<otp>[^"]*)")?')
def step_impl(context, email, refund_id, otp=None):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    body = {}
    if otp:
        body["otp"] = otp

    response = context.api_client.post(
        f"/api/v1/admin/finance/refunds/{refund_id}/approve",
        json=body if body else None,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


# Restore default matcher so subsequent step registrations are unaffected
use_step_matcher("parse")
