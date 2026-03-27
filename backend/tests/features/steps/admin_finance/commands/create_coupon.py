"""When 使用者建立優惠碼 — Command (POST)"""

import re
from behave import use_step_matcher, when, step

use_step_matcher("re")


@when(r'使用者 "(?P<email>[^"]+)" 建立優惠碼，代碼為 (?P<code>[^，]*)，折扣類型為 (?P<discount_type>[^，]*)，折扣值為 (?P<discount_value>[^，]*)')
def step_impl_outline(context, email, code, discount_type, discount_value):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    payload = {}
    code = code or ""
    discount_type = discount_type or ""
    discount_value = discount_value or ""
    if code.strip():
        payload["code"] = code.strip()
    if discount_type.strip():
        payload["discount_type"] = discount_type.strip()
    if discount_value.strip():
        payload["discount_value"] = float(discount_value.strip())

    response = context.api_client.post(
        "/api/v1/admin/finance/coupons",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")


@when('使用者 "{email}" 建立優惠碼：')
def step_impl_table(context, email):
    actor_id = context.ids[email]
    token = context.jwt_helper.generate_token(actor_id)

    data = {}
    for row in context.table:
        field = row["欄位"]
        value = row["值"]
        if field in ("discount_value",):
            data[field] = float(value)
        elif field in ("max_uses", "max_uses_per_user"):
            data[field] = int(value)
        else:
            data[field] = value

    response = context.api_client.post(
        "/api/v1/admin/finance/coupons",
        json=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
