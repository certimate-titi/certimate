"""When 系統收到綠界付款成功回呼 — Command"""

from behave import when

from app.services.ecpay_service import ECPayService


@when('系統收到綠界付款成功回呼 (RtnCode=1)')
def step_impl(context):
    trade_no = context.memo.get("last_pending_trade_no", "")

    # 構建回呼參數
    params = {
        "MerchantTradeNo": trade_no,
        "RtnCode": "1",
        "TradeNo": "2026032610009999",
        "TradeAmt": "199",
        "PaymentType": "Credit_CreditCard",
    }

    # 計算真實 CheckMacValue
    service = ECPayService(context.db_session)
    params["CheckMacValue"] = service._calculate_mac(params)

    response = context.api_client.post(
        "/api/v1/ecpay/callback",
        data=params,
    )
    context.last_response = response
    context.memo["last_callback_data"] = params
