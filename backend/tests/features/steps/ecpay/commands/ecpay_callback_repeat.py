"""When 綠界再次發送相同的回呼至 ReturnURL — Command"""

from behave import when

from app.services.ecpay_service import ECPayService


@when('綠界再次發送相同的回呼至 ReturnURL')
def step_impl(context):
    # 重發上一次的回呼資料（已包含正確的 CheckMacValue）
    callback_data = context.memo.get("last_callback_data", {})

    if not callback_data:
        # 沒有之前的回呼資料，構建一份並計算真實 MAC
        trade_no = context.memo.get("last_callback_trade_no", "CRT20260326100001")
        params = {
            "MerchantTradeNo": trade_no,
            "RtnCode": "1",
            "TradeNo": "2026032610001234",
            "TradeAmt": "199",
            "PaymentType": "Credit_CreditCard",
        }
        service = ECPayService(context.db_session)
        params["CheckMacValue"] = service._calculate_mac(params)
        callback_data = params

    response = context.api_client.post(
        "/api/v1/ecpay/callback",
        data=callback_data,
    )
    context.last_response = response
