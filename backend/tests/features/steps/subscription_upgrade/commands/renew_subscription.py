"""When 系統在下次扣款日成功續訂 — Command"""

import uuid

from behave import when

from app.services.ecpay_service import ECPayService
from app.models.transaction import Transaction
from decimal import Decimal


@when('系統在下次扣款日成功續訂')
def step_impl(context):
    email = context.memo.get("last_pending_email", "pro@example.com")
    if email not in context.ids:
        email = "pro@example.com"
    user_uuid = uuid.UUID(context.ids[email])
    db = context.db_session

    trade_no = "CRT_RENEW_001"[:20]

    txn = Transaction(
        user_id=user_uuid,
        merchant_trade_no=trade_no,
        target_plan="PRO_199",
        amount=Decimal("199"),
        status="pending",
        payment_provider="ecpay",
    )
    db.add(txn)
    db.commit()

    params = {
        "MerchantTradeNo": trade_no,
        "RtnCode": "1",
        "TradeNo": "2026042610001234",
        "TradeAmt": "199",
        "PaymentType": "Credit_CreditCard",
    }

    service = ECPayService(db)
    params["CheckMacValue"] = service._calculate_mac(params)

    response = context.api_client.post(
        "/api/v1/ecpay/callback",
        data=params,
    )
    context.last_response = response
    context.memo["renewal_email"] = email
