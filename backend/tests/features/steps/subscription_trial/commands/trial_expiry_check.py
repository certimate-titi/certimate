"""When — 系統執行試用到期檢查排程。"""

from datetime import datetime, timezone
from unittest.mock import patch

from behave import when


@when('系統執行試用到期檢查排程，當前日期為 {date}')
def step_trial_expiry_check(context, date):
    from app.services.trial_service import TrialService

    mock_now = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)

    with patch('app.services.trial_service.datetime') as mock_dt:
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        service = TrialService(context.db_session)
        context.memo["trial_expiry_result"] = service.check_and_expire_trials(mock_now)
