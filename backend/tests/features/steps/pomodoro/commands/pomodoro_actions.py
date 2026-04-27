"""When 番茄鐘操作 — Commands

番茄鐘為純前端功能（localStorage 儲存設定 + 客戶端計時）。
以下 step 僅操作 context.memo，不呼叫後端 API。
例外：`使用者查看測驗結果` / `使用者查看個人儀表板` 會呼叫實際 API，
但番茄鐘摘要資料由前端組裝，此處 Then step 以 memo 驗證而非 response。
"""

from behave import when


FOCUS_MIN, FOCUS_MAX = 15, 60


def _fake_ok(context):
    context.last_response = type(
        "FakeResp", (), {
            "status_code": 200,
            "json": lambda self: {},
            "text": "",
        },
    )()


def _fake_error(context, message, status=400):
    context.last_response = type(
        "FakeResp", (), {
            "status_code": status,
            "json": lambda self: {"message": message},
            "text": message,
        },
    )()


@when('使用者 "{email}" 啟用番茄鐘模式')
def step_impl_enable_pomodoro(context, email):
    context.memo["current_user_email"] = email
    context.memo["pomodoro_settings"] = {
        "enabled": True,
        "focus_minutes": 25,
        "short_break_minutes": 5,
        "long_break_minutes": 15,
        "long_break_interval": 4,
    }
    _fake_ok(context)


@when('使用者 "{email}" 設定番茄鐘為專注 {focus:d} 分鐘、短休息 {short_break:d} 分鐘、長休息 {long_break:d} 分鐘')
def step_impl_set_pomodoro(context, email, focus, short_break, long_break):
    if not (FOCUS_MIN <= focus <= FOCUS_MAX):
        _fake_error(context, "專注時長需介於 15 至 60 分鐘")
        return
    context.memo["current_user_email"] = email
    context.memo["pomodoro_settings"] = {
        "enabled": True,
        "focus_minutes": focus,
        "short_break_minutes": short_break,
        "long_break_minutes": long_break,
        "long_break_interval": 4,
    }
    _fake_ok(context)


@when('使用者 "{email}" 設定番茄鐘專注時長為 {minutes:d} 分鐘')
def step_impl_set_invalid_focus(context, email, minutes):
    if not (FOCUS_MIN <= minutes <= FOCUS_MAX):
        _fake_error(context, "專注時長需介於 15 至 60 分鐘")
        return
    settings = context.memo.setdefault("pomodoro_settings", {"enabled": True})
    settings["focus_minutes"] = minutes
    _fake_ok(context)


@when('使用者 "{email}" 開始測驗 {exam_id:d}（{duration:d} 分鐘）')
def step_impl_start_exam_with_duration(context, email, exam_id, duration):
    context.memo["current_user_email"] = email
    context.memo["current_exam_id"] = exam_id
    context.memo["current_exam_duration"] = duration
    settings = context.memo.get("pomodoro_settings", {})
    focus = settings.get("focus_minutes", 25)
    # 考試時長 < 專注時段 → 計時器自動隱藏
    context.memo["pomodoro_timer_visible"] = duration >= focus
    _fake_ok(context)


@when('番茄專注時段結束')
def step_impl_focus_ended(context):
    n = context.memo.get("pomodoro_session_count", 1)
    settings = context.memo.get("pomodoro_settings", {})
    interval = settings.get("long_break_interval", 4)
    is_long = n > 0 and n % interval == 0
    focus = settings.get("focus_minutes", 25)
    short_b = settings.get("short_break_minutes", 5)
    long_b = settings.get("long_break_minutes", 15)
    context.memo["pomodoro_notification"] = {
        "shown": True,
        "message": (
            f"太棒了！已完成 {n} 個番茄鐘 🍅🍅🍅🍅 建議長休息 {long_b} 分鐘"
            if is_long
            else f"已專注 {focus} 分鐘，建議休息 {short_b} 分鐘 🌿"
        ),
        "actions": [{"label": "開始休息"}, {"label": "繼續作答"}],
        "is_long_break": is_long,
    }
    if is_long:
        context.memo["pomodoro_timer"] = {
            "mode": "long_break",
            "status": "休息中",
            "remaining_seconds": long_b * 60,
        }


@when('第 {n:d} 個專注時段結束')
def step_impl_nth_focus_ended(context, n):
    context.memo["pomodoro_session_count"] = n
    step_impl_focus_ended(context)


@when('使用者點擊「繼續作答」')
def step_impl_skip_break(context):
    context.memo["pomodoro_timer"] = {
        "mode": "focus",
        "status": "專注中",
    }
    context.memo["break_skipped"] = True


@when('使用者點擊「開始休息」')
def step_impl_start_break(context):
    settings = context.memo.get("pomodoro_settings", {})
    notif = context.memo.get("pomodoro_notification", {})
    is_long = notif.get("is_long_break", False)
    minutes = settings.get("long_break_minutes", 15) if is_long \
        else settings.get("short_break_minutes", 5)
    context.memo["pomodoro_timer"] = {
        "mode": "long_break" if is_long else "break",
        "status": "休息中",
        "remaining_seconds": minutes * 60,
    }
    context.memo["exam_timer_running"] = True
    context.memo["break_overlay_visible"] = True


@when('使用者完成第 {n:d} 個番茄鐘')
def step_impl_complete_nth_pomodoro(context, n):
    email = context.memo.get("current_user_email", "pro@example.com")
    total = context.memo.get(f"total_pomodoros_{email}", 0) + 1
    context.memo[f"total_pomodoros_{email}"] = total
    if total >= 50:
        context.memo["unlocked_achievements"] = [{
            "name": "番茄達人",
            "description": "累計完成 50 個番茄鐘，專注力驚人！",
        }]


@when('使用者查看測驗結果')
def step_impl_view_exam_results(context):
    from app.models.user import User
    email = context.memo.get("current_user_email", "pro@example.com")
    exam_id = context.memo.get("current_exam_id", 1)
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type(
            "FakeResp", (), {"status_code": 404, "json": lambda self: {}, "text": ""}
        )()
        return
    token = context.jwt_helper.generate_token(str(user.id))
    exam_key = f"exam_id_{exam_id}"
    exam_uuid = context.ids.get(exam_key, str(exam_id))
    response = context.api_client.get(
        f"/api/v1/exams/{exam_uuid}/results",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者查看個人儀表板')
def step_impl_view_dashboard(context):
    from app.models.user import User
    email = context.memo.get("current_user_email", "pro@example.com")
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type(
            "FakeResp", (), {"status_code": 404, "json": lambda self: {}, "text": ""}
        )()
        return
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('休息畫面顯示')
def step_impl_break_screen(context):
    context.memo["break_screen"] = {
        "countdown_ring": True,
        "progress_summary": "目前已完成 15/50 題，答對率 80%",
        "fun_fact": True,
        "close_button": True,
    }


@when('使用者作答題目')
def step_impl_answer_question(context):
    context.memo["action"] = "answering_question"
    # 開始作答時顯示計時器視覺狀態
    settings = context.memo.get("pomodoro_settings", {})
    if settings.get("enabled"):
        context.memo.setdefault("pomodoro_timer", {
            "mode": "focus",
            "status": "專注中",
            "visible": True,
            "shape": "circle",
            "position": "top-right",
            "overlap_content": False,
            "color_focus": "green",
            "color_break": "blue",
        })
