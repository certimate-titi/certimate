"""When 系統處理完付款成功回呼並升級至 / 系統處理完升級 — Command"""

import uuid

from behave import when

from app.services.ecpay_service import ECPayService
from app.models.transaction import Transaction
from decimal import Decimal


@when('系統處理完付款成功回呼並升級至 {plan}')
def step_impl(context, plan):
    email = context.memo.get("last_pending_email", "free@example.com")
    user_uuid = uuid.UUID(context.ids[email])
    db = context.db_session

    # 確保有 pending 交易
    trade_no = context.memo.get("last_pending_trade_no")
    if not trade_no:
        trade_no = f"CRT_UPGRADE_{plan}"[:20]
        txn = Transaction(
            user_id=user_uuid,
            merchant_trade_no=trade_no,
            target_plan=plan,
            amount=Decimal("199"),
            status="pending",
            payment_provider="ecpay",
        )
        db.add(txn)
        db.commit()
        context.memo["last_pending_trade_no"] = trade_no

    # 構建回呼參數
    params = {
        "MerchantTradeNo": trade_no,
        "RtnCode": "1",
        "TradeNo": "2026032610009999",
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

    # 記錄 Firebase Claims 更新
    if "firebase_claims" not in context.memo:
        context.memo["firebase_claims"] = {}
    context.memo["firebase_claims"][email] = {
        "plan": plan,
        "subscription_status": "active",
    }


@when('系統處理完 "{email}" 的升級至 {plan}')
def step_impl_specific(context, email, plan):
    user_uuid = uuid.UUID(context.ids[email])
    db = context.db_session

    trade_no = f"CRT_UPG_{email[:3].upper()}"[:20]
    txn = Transaction(
        user_id=user_uuid,
        merchant_trade_no=trade_no,
        target_plan=plan,
        amount=Decimal("199"),
        status="pending",
        payment_provider="ecpay",
    )
    db.add(txn)
    db.commit()

    params = {
        "MerchantTradeNo": trade_no,
        "RtnCode": "1",
        "TradeNo": "2026032610009998",
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
    context.memo["last_upgrade_trade_no"] = trade_no
