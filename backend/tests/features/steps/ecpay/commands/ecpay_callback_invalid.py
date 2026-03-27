"""When 綠界發送回呼至 ReturnURL（無效 CheckMacValue）— Command"""

from behave import when

from app.models.transaction import Transaction


@when('綠界發送回呼至 ReturnURL，但 CheckMacValue 為無效值 "{fake_mac}"')
def step_impl(context, fake_mac):
    db = context.db_session
    # 找到一筆 pending 交易作為回呼目標
    txn = db.query(Transaction).filter_by(status="pending").first()
    trade_no = txn.merchant_trade_no if txn else "UNKNOWN"

    # 記錄回呼前的狀態
    context.memo["pre_callback_status"] = txn.status if txn else None

    response = context.api_client.post(
        "/api/v1/ecpay/callback",
        data={
            "MerchantTradeNo": trade_no,
            "RtnCode": "1",
            "TradeNo": "0000000000000000",
            "TradeAmt": "199",
            "CheckMacValue": fake_mac,
        },
    )
    context.last_response = response
