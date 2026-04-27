"""Given 番茄鐘狀態前置條件 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已啟用番茄鐘模式（專注 {minutes:d} 分鐘）')
def step_impl_pomodoro_enabled(context, email, minutes):
    """設定使用者已啟用番茄鐘模式。"""
    context.memo[f"pomodoro_enabled_{email}"] = True
    context.memo[f"pomodoro_focus_minutes_{email}"] = minutes
    context.memo["current_user_email"] = email
    context.memo["pomodoro_settings"] = {
        "enabled": True,
        "focus_minutes": minutes,
        "short_break_minutes": 5,
        "long_break_minutes": 15,
        "long_break_interval": 4,
    }


@given('使用者 "{email}" 正在進行測驗 {exam_id:d}，番茄計時器剩餘 0 秒')
def step_impl_pomodoro_ending(context, email, exam_id):
    """設定使用者正在進行測驗且番茄計時器即將結束。"""
    context.memo["current_user_email"] = email
    context.memo["current_exam_id"] = exam_id
    context.memo["pomodoro_timer_remaining"] = 0


@given('使用者 "{email}" 收到番茄鐘休息提醒')
def step_impl_pomodoro_break_reminder(context, email):
    """設定使用者已收到番茄鐘休息提醒。"""
    context.memo["current_user_email"] = email
    context.memo["pomodoro_break_reminder"] = True


@given('使用者 "{email}" 已完成 {count:d} 個番茄專注時段')
def step_impl_completed_sessions(context, email, count):
    """設定使用者已完成指定數量的番茄專注時段。"""
    context.memo[f"pomodoro_completed_{email}"] = count
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 完成測驗 {exam_id:d}，過程中完成 {pomodoro_count:d} 個番茄鐘、跳過 {skipped:d} 次休息')
def step_impl_exam_pomodoro_summary(context, email, exam_id, pomodoro_count, skipped):
    """設定測驗結果含番茄鐘統計。"""
    context.memo["current_user_email"] = email
    context.memo["current_exam_id"] = exam_id
    context.memo["exam_pomodoro_count"] = pomodoro_count
    context.memo["exam_skipped_breaks"] = skipped


@given('使用者 "{email}" 本週已完成 {count:d} 個番茄鐘')
def step_impl_weekly_pomodoros(context, email, count):
    """設定使用者本週已完成指定數量的番茄鐘。"""
    context.memo[f"weekly_pomodoros_{email}"] = count
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 已累計完成 {count:d} 個番茄鐘')
def step_impl_total_pomodoros(context, email, count):
    """設定使用者累計完成的番茄鐘數量。"""
    context.memo[f"total_pomodoros_{email}"] = count
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 進入番茄鐘休息時段')
def step_impl_enter_break(context, email):
    """設定使用者進入休息時段。"""
    context.memo["current_user_email"] = email
    context.memo["pomodoro_in_break"] = True


@given('使用者 "{email}" 已開始測驗 {exam_id:d}，番茄鐘啟用中')
def step_impl_exam_started_with_pomodoro(context, email, exam_id):
    """設定使用者開始測驗且番茄鐘啟用中。"""
    context.memo["current_user_email"] = email
    context.memo["current_exam_id"] = exam_id
    context.memo[f"pomodoro_enabled_{email}"] = True
    context.memo.setdefault("pomodoro_settings", {
        "enabled": True,
        "focus_minutes": 25,
        "short_break_minutes": 5,
        "long_break_minutes": 15,
        "long_break_interval": 4,
    })
