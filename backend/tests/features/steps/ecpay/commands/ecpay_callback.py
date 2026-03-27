"""When 綠界發送回呼至 ReturnURL — Command"""

from behave import when

from app.services.ecpay_service import ECPayService


@when('綠界發送回呼至 ReturnURL：')
def step_impl(context):
    callback_data = {}
    for row in context.table:
        field = row["欄位"]
        value = row["值"]
        callback_data[field] = value

    # 若有動態 CheckMacValue 佔位符，計算真實值
    if callback_data.get("CheckMacValue") == "(有效的 CheckMacValue)":
        params_for_mac = {k: v for k, v in callback_data.items() if k != "CheckMacValue"}
        service = ECPayService(context.db_session)
        callback_data["CheckMacValue"] = service._calculate_mac(params_for_mac)

    # 記錄 trade_no 供後續驗證
    trade_no = callback_data.get("MerchantTradeNo", "")
    context.memo["last_callback_trade_no"] = trade_no
    context.memo["last_callback_data"] = callback_data

    response = context.api_client.post(
        "/api/v1/ecpay/callback",
        data=callback_data,
    )
    context.last_response = response
