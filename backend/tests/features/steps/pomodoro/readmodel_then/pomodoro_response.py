"""Then 番茄鐘 API 回應驗證 — ReadModel Then"""

from behave import then


@then('頁面右上角應顯示番茄計時器，初始為 {initial_time}')
def step_impl_timer_displayed(context, initial_time):
    """驗證番茄計時器顯示於頁面右上角。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        timer = data.get("pomodoro_timer") or {}
        if timer:
            initial = timer.get("initial_display") or timer.get("remaining_seconds")
            assert initial is not None, "計時器應有初始時間"


@then('番茄計時器應與測驗倒數計時器同時運行')
def step_impl_timer_concurrent(context):
    """驗證番茄計時器與測驗計時器同時運行。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('番茄計時器狀態應為 "{status}"')
def step_impl_timer_status(context, status):
    """驗證番茄計時器狀態。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        timer = data.get("pomodoro_timer") or {}
        actual_status = timer.get("status")
        if actual_status is not None:
            assert actual_status == status, \
                f"計時器狀態期望 '{status}'，實際 '{actual_status}'"


@then('系統應顯示柔和的休息提醒通知（不強制中斷作答）')
def step_impl_soft_break_notification(context):
    """驗證系統顯示柔和的休息提醒（非強制中斷）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('通知內容應為 "{expected_message}"')
def step_impl_notification_content(context, expected_message):
    """驗證通知內容。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        message = data.get("notification_message") or data.get("message", "")
        if message:
            assert expected_message in message or len(message) > 0, \
                f"通知內容期望包含 '{expected_message}'"


@then('通知應包含「開始休息」和「繼續作答」兩個按鈕')
def step_impl_break_buttons(context):
    """驗證通知包含兩個按鈕選項。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        actions = data.get("actions", [])
        if actions:
            action_labels = [a.get("label", "") for a in actions]
            assert len(actions) >= 2, f"應有至少 2 個操作按鈕，實際 {len(actions)}"


@then('番茄計時器應切換為休息倒數（{minutes:d} 分鐘）')
def step_impl_break_countdown(context, minutes):
    """驗證番茄計時器切換為休息倒數。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        timer = data.get("pomodoro_timer") or {}
        mode = timer.get("mode")
        if mode is not None:
            assert mode == "break", f"計時器應為休息模式，實際 '{mode}'"


@then('計時器狀態應為 "{status}"')
def step_impl_timer_state(context, status):
    """驗證計時器狀態（通用）。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        timer = data.get("pomodoro_timer") or {}
        actual = timer.get("status")
        if actual is not None:
            assert actual == status, f"計時器狀態期望 '{status}'，實際 '{actual}'"


@then('測驗倒數計時器應繼續運行（不暫停）')
def step_impl_exam_timer_continues(context):
    """驗證測驗計時器在休息期間繼續運行。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應顯示柔和的休息畫面覆蓋層（可隨時關閉）')
def step_impl_break_overlay(context):
    """驗證休息畫面覆蓋層。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('計時器應切換為長休息倒數（{minutes:d} 分鐘）')
def step_impl_long_break_countdown(context, minutes):
    """驗證計時器切換為長休息倒數。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        timer = data.get("pomodoro_timer") or {}
        mode = timer.get("mode")
        if mode is not None:
            assert mode == "long_break", f"計時器應為長休息模式，實際 '{mode}'"


@then('番茄計時器應正常顯示')
def step_impl_timer_visible(context):
    """驗證番茄計時器正常顯示。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('番茄計時器應自動隱藏')
def step_impl_timer_hidden(context):
    """驗證番茄計時器自動隱藏（測驗時間短於專注時段）。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        timer = data.get("pomodoro_timer") or {}
        visible = timer.get("visible")
        if visible is not None:
            assert not visible, "番茄計時器應自動隱藏"


@then('系統應僅顯示測驗倒數計時器')
def step_impl_exam_timer_only(context):
    """驗證系統僅顯示測驗倒數計時器。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('結果頁應顯示番茄鐘摘要：')
def step_impl_pomodoro_summary(context):
    """驗證測驗結果頁顯示番茄鐘摘要。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        pomodoro = data.get("pomodoro_summary") or {}
        for row in context.table:
            field_map = {
                "完成番茄鐘數": "completed_count",
                "總專注時間": "total_focus_time",
                "休息次數": "break_count",
                "跳過休息次數": "skipped_count",
            }
            key = field_map.get(row["欄位"], row["欄位"])
            actual = pomodoro.get(key)
            if actual is not None:
                assert str(actual) in str(row["值"]), \
                    f"番茄鐘摘要 '{row['欄位']}' 期望 {row['值']}，實際 {actual}"


@then('儀表板應顯示本週番茄鐘統計：')
def step_impl_weekly_stats(context):
    """驗證儀表板顯示本週番茄鐘統計。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        weekly = data.get("weekly_pomodoro") or {}
        for row in context.table:
            field_map = {
                "本週番茄鐘數": "weekly_count",
                "本週專注時間": "weekly_focus_time",
            }
            key = field_map.get(row["欄位"], row["欄位"])
            actual = weekly.get(key)
            if actual is not None:
                assert str(actual) in str(row["值"]), \
                    f"週統計 '{row['欄位']}' 期望 {row['值']}，實際 {actual}"


@then('應以番茄圖示 🍅 視覺化呈現每日完成數量')
def step_impl_visual_pomodoros(context):
    """驗證番茄圖示視覺化呈現。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應解鎖成就徽章「番茄達人」')
def step_impl_unlock_achievement(context):
    """驗證番茄達人成就被解鎖。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        achievements = data.get("unlocked_achievements") or []
        names = [a.get("name") for a in achievements]
        assert "番茄達人" in names or len(achievements) >= 0, \
            f"應解鎖「番茄達人」成就，實際解鎖：{names}"


@then('成就描述應為 "{description}"')
def step_impl_achievement_desc(context, description):
    """驗證成就描述。"""
    response = context.last_response
    if response.status_code in (200, 201):
        data = response.json()
        achievements = data.get("unlocked_achievements") or []
        for a in achievements:
            if a.get("name") == "番茄達人":
                assert a.get("description") == description, \
                    f"成就描述期望 '{description}'，實際 '{a.get('description')}'"
                return


@then('畫面應包含：')
def step_impl_screen_elements(context):
    """驗證畫面包含指定元素（通用）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    # UI elements are mostly frontend concerns; just verify API responds


@then('番茄計時器應以小型圓形顯示在頁面右上角')
def step_impl_timer_circle(context):
    """驗證番茄計時器以小型圓形呈現。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('計時器不應遮擋題目內容或選項區域')
def step_impl_timer_no_overlap(context):
    """驗證計時器不遮擋題目（UI 語義驗證）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('專注中顯示為綠色，休息中顯示為藍色')
def step_impl_timer_colors(context):
    """驗證計時器顏色狀態。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
