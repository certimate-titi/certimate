"""Then 番茄鐘狀態驗證 — Aggregate Then

純前端 memo 驗證（Pomodoro 為純客戶端功能，不呼叫後端）。
"""

from behave import then


FIELD_MAP = {
    "專注時長（分鐘）": "focus_minutes",
    "短休息（分鐘）": "short_break_minutes",
    "長休息（分鐘）": "long_break_minutes",
    "長休息間隔": "long_break_interval",
    "啟用狀態": "enabled",
}


@then('使用者的番茄鐘設定應為：')
def step_impl_pomodoro_settings(context):
    settings = context.memo.get("pomodoro_settings")
    assert settings, "memo 無 pomodoro_settings"
    for row in context.table:
        key = FIELD_MAP.get(row["欄位"], row["欄位"])
        expected = row["值"]
        actual = settings.get(key)
        assert str(actual).lower() == str(expected).lower(), \
            f"番茄鐘設定 '{row['欄位']}' 期望 {expected}，實際 {actual}"


@then('使用者的番茄鐘設定專注時長應為 {minutes:d}')
def step_impl_focus_minutes(context, minutes):
    settings = context.memo.get("pomodoro_settings", {})
    actual = settings.get("focus_minutes")
    assert actual == minutes, f"專注時長期望 {minutes}，實際 {actual}"


@then('番茄計時器應重新開始下一個專注時段')
def step_impl_new_focus_session(context):
    timer = context.memo.get("pomodoro_timer", {})
    assert timer.get("mode") == "focus" and timer.get("status") == "專注中", \
        f"計時器應為專注狀態，實際 {timer}"


@then('該次休息應記錄為 "已跳過"')
def step_impl_break_skipped(context):
    assert context.memo.get("break_skipped") is True, "休息應記錄為已跳過"
