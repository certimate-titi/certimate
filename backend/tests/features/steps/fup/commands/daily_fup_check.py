"""When — 系統執行每日 FUP 檢查排程。"""

from unittest.mock import MagicMock

from behave import when


@when('系統執行每日 FUP 檢查排程')
def step_daily_fup_check(context):
    from app.services.fup_service import FUPService
    service = FUPService(context.db_session)
    result = service.run_daily_check()
    context.memo["fup_result"] = result

    # Set a mock response so Then steps that check context.last_response work
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = result
    mock_response.text = str(result)
    context.last_response = mock_response
