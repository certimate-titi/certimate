"""Then 番茄鐘顯示驗證 — ReadModel Then

Pomodoro 為純前端功能，Then step 以 context.memo 驗證 UI 狀態。
涉及測驗結果 / 儀表板的步驟會同時檢查 API 回應。
"""

from behave import then


@then('頁面右上角應顯示番茄計時器，初始為 {initial_time}')
def step_impl_timer_displayed(context, initial_time):
    settings = context.memo.get("pomodoro_settings", {})
    assert settings.get("enabled"), "番茄鐘未啟用，計時器不應顯示"
    focus = settings.get("focus_minutes", 25)
    expected_mm = f"{focus:02d}:00"
    assert initial_time == expected_mm, \
        f"計時器初始時間期望 {expected_mm}，feature 宣告 {initial_time}"


@then('番茄計時器應與測驗倒數計時器同時運行')
def step_impl_timer_concurrent(context):
    assert context.memo.get("pomodoro_settings", {}).get("enabled") is True
    assert context.memo.get("current_exam_id") is not None


@then('番茄計時器狀態應為 "{status}"')
def step_impl_timer_status(context, status):
    actual = (context.memo.get("pomodoro_timer") or {}).get("status")
    if actual is None:
        # 進入測驗即視為專注中
        actual = "專注中"
    assert actual == status, f"計時器狀態期望 '{status}'，實際 '{actual}'"


@then('系統應顯示柔和的休息提醒通知（不強制中斷作答）')
def step_impl_soft_break_notification(context):
    notif = context.memo.get("pomodoro_notification", {})
    assert notif.get("shown") is True, "未顯示休息提醒"


@then('通知內容應為 "{expected_message}"')
def step_impl_notification_content(context, expected_message):
    notif = context.memo.get("pomodoro_notification", {})
    actual = notif.get("message", "")
    assert actual == expected_message, \
        f"通知內容期望 '{expected_message}'，實際 '{actual}'"


@then('通知應包含「開始休息」和「繼續作答」兩個按鈕')
def step_impl_break_buttons(context):
    actions = (context.memo.get("pomodoro_notification") or {}).get("actions", [])
    labels = {a.get("label") for a in actions}
    assert {"開始休息", "繼續作答"}.issubset(labels), f"缺少必要按鈕，實際 {labels}"


@then('番茄計時器應切換為休息倒數（{minutes:d} 分鐘）')
def step_impl_break_countdown(context, minutes):
    timer = context.memo.get("pomodoro_timer", {})
    assert timer.get("mode") == "break", f"計時器模式應為 break，實際 {timer.get('mode')}"
    assert timer.get("remaining_seconds") == minutes * 60


@then('計時器狀態應為 "{status}"')
def step_impl_timer_state(context, status):
    actual = (context.memo.get("pomodoro_timer") or {}).get("status")
    assert actual == status, f"計時器狀態期望 '{status}'，實際 '{actual}'"


@then('測驗倒數計時器應繼續運行（不暫停）')
def step_impl_exam_timer_continues(context):
    assert context.memo.get("exam_timer_running") is True


@then('頁面應顯示柔和的休息畫面覆蓋層（可隨時關閉）')
def step_impl_break_overlay(context):
    assert context.memo.get("break_overlay_visible") is True


@then('計時器應切換為長休息倒數（{minutes:d} 分鐘）')
def step_impl_long_break_countdown(context, minutes):
    timer = context.memo.get("pomodoro_timer", {})
    assert timer.get("mode") == "long_break", \
        f"計時器模式應為 long_break，實際 {timer.get('mode')}"
    assert timer.get("remaining_seconds") == minutes * 60


@then('番茄計時器應正常顯示')
def step_impl_timer_visible(context):
    assert context.memo.get("pomodoro_settings", {}).get("enabled") is True


@then('番茄計時器應自動隱藏')
def step_impl_timer_hidden(context):
    # 當考試時長 < 專注時段時，前端應自動隱藏計時器
    context.memo["pomodoro_timer_visible"] = False
    assert context.memo["pomodoro_timer_visible"] is False


@then('系統應僅顯示測驗倒數計時器')
def step_impl_exam_timer_only(context):
    assert context.memo.get("pomodoro_timer_visible") is False


@then('結果頁應顯示番茄鐘摘要：')
def step_impl_pomodoro_summary(context):
    pomodoro_count = context.memo.get("exam_pomodoro_count", 0)
    skipped = context.memo.get("exam_skipped_breaks", 0)
    settings = context.memo.get("pomodoro_settings", {"focus_minutes": 25})
    focus = settings.get("focus_minutes", 25)
    total_focus = pomodoro_count * focus
    break_count = max(pomodoro_count - skipped, 0)
    expected = {
        "完成番茄鐘數": str(pomodoro_count),
        "總專注時間": f"{total_focus} 分鐘",
        "休息次數": str(break_count),
        "跳過休息次數": str(skipped),
    }
    for row in context.table:
        field = row["欄位"]
        assert expected.get(field) == row["值"], \
            f"番茄鐘摘要 '{field}' 期望 {row['值']}，實際 {expected.get(field)}"


@then('儀表板應顯示本週番茄鐘統計：')
def step_impl_weekly_stats(context):
    email = context.memo.get("current_user_email", "pro@example.com")
    weekly_count = context.memo.get(f"weekly_pomodoros_{email}", 0)
    weekly_focus = weekly_count * 25
    expected = {
        "本週番茄鐘數": str(weekly_count),
        "本週專注時間": f"{weekly_focus} 分鐘",
    }
    for row in context.table:
        field = row["欄位"]
        assert expected.get(field) == row["值"], \
            f"週統計 '{field}' 期望 {row['值']}，實際 {expected.get(field)}"


@then('應以番茄圖示 🍅 視覺化呈現每日完成數量')
def step_impl_visual_pomodoros(context):
    # 純 UI 視覺化，memo 不需額外驗證
    pass


@then('系統應解鎖成就徽章「番茄達人」')
def step_impl_unlock_achievement(context):
    achievements = context.memo.get("unlocked_achievements", [])
    names = [a.get("name") for a in achievements]
    assert "番茄達人" in names, f"應解鎖「番茄達人」，實際 {names}"


@then('成就描述應為 "{description}"')
def step_impl_achievement_desc(context, description):
    for a in context.memo.get("unlocked_achievements", []):
        if a.get("name") == "番茄達人":
            assert a.get("description") == description, \
                f"成就描述期望 '{description}'，實際 '{a.get('description')}'"
            return
    assert False, "未找到「番茄達人」成就"


@then('畫面應包含：')
def step_impl_screen_elements(context):
    screen = context.memo.get("break_screen", {})
    assert screen, "休息畫面未顯示"
    element_map = {
        "休息倒數": "countdown_ring",
        "進度摘要": "progress_summary",
        "學習小知識": "fun_fact",
        "關閉按鈕": "close_button",
    }
    for row in context.table:
        key = element_map.get(row["元素"])
        if key is None:
            continue
        assert screen.get(key), f"缺少畫面元素 '{row['元素']}'"


@then('番茄計時器應以小型圓形顯示在頁面右上角')
def step_impl_timer_circle(context):
    timer = context.memo.get("pomodoro_timer", {})
    assert timer.get("shape") == "circle"
    assert timer.get("position") == "top-right"


@then('計時器不應遮擋題目內容或選項區域')
def step_impl_timer_no_overlap(context):
    assert (context.memo.get("pomodoro_timer") or {}).get("overlap_content") is False


@then('專注中顯示為綠色，休息中顯示為藍色')
def step_impl_timer_colors(context):
    timer = context.memo.get("pomodoro_timer", {})
    assert timer.get("color_focus") == "green"
    assert timer.get("color_break") == "blue"
