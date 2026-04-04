"""Then — 驗證告警內容包含使用者 Email 與連續觸發天數。"""

from behave import then


@then('告警內容應包含使用者 Email 與連續觸發天數')
def step_alert_content(context):
    fup_result = context.memo.get("fup_result", {})

    # The FUP check result should contain alerts with email and consecutive days
    alerts = fup_result.get("alerts", []) if isinstance(fup_result, dict) else []
    assert len(alerts) > 0, \
        f"預期有告警內容，但 fup_result ��: {fup_result}"

    for alert in alerts:
        assert "email" in alert or "user_email" in alert, \
            f"告警缺少 email 欄位: {alert}"
        assert "consecutive_days" in alert or "days" in alert, \
            f"告警缺少連續天數欄位: {alert}"
