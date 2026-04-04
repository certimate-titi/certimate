"""When — FUP 用量檢查。"""

from behave import when


@when('系統執行 FUP 每日用量檢查')
def step_fup_daily_check(context):
    from app.services.fup_service import FUPService
    service = FUPService(context.db_session)
    context.memo["fup_result"] = service.run_daily_check()


@when('使用者 "{email}" 檢查 FUP 用量')
def step_check_fup(context, email):
    token = context.jwt_helper.generate_token(context.ids.get(email, email))
    context.last_response = context.api_client.get(
        "/api/v1/subscriptions/fup/check",
        headers={"Authorization": f"Bearer {token}"},
    )
