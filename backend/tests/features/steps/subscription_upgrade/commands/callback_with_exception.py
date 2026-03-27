"""When 系統收到綠界付款成功回呼但資料庫更新拋出異常 — Command"""

from unittest.mock import patch

from behave import when

from app.services.ecpay_service import ECPayService


@when('系統收到綠界付款成功回呼 (RtnCode=1) 但資料庫更新拋出異常')
def step_impl(context):
    trade_no = context.memo.get("last_pending_trade_no", "")

    params = {
        "MerchantTradeNo": trade_no,
        "RtnCode": "1",
        "TradeNo": "2026032610009999",
        "TradeAmt": "199",
        "PaymentType": "Credit_CreditCard",
    }

    service = ECPayService(context.db_session)
    params["CheckMacValue"] = service._calculate_mac(params)

    response = context.api_client.post(
        "/api/v1/ecpay/callback",
        data=params,
    )
    context.last_response = response
    context.memo["exception_trade_no"] = trade_no
