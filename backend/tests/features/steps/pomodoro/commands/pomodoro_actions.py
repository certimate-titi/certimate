"""When 番茄鐘操作 — Commands"""

from behave import when


@when('使用者 "{email}" 啟用番茄鐘模式')
def step_impl_enable_pomodoro(context, email):
    """呼叫 API 啟用番茄鐘模式。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/pomodoro/settings",
        json={"enabled": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_user_email"] = email


@when('使用者 "{email}" 設定番茄鐘為專注 {focus:d} 分鐘、短休息 {short_break:d} 分鐘、長休息 {long_break:d} 分鐘')
def step_impl_set_pomodoro(context, email, focus, short_break, long_break):
    """呼叫 API 設定自訂番茄鐘時間。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/pomodoro/settings",
        json={
            "enabled": True,
            "focus_minutes": focus,
            "short_break_minutes": short_break,
            "long_break_minutes": long_break,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 設定番茄鐘專注時長為 {minutes:d} 分鐘')
def step_impl_set_invalid_focus(context, email, minutes):
    """呼叫 API 設定無效的番茄鐘專注時長。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/pomodoro/settings",
        json={"enabled": True, "focus_minutes": minutes},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


# 注意："使用者 開始測驗" step 已定義於 mock_exam/commands/start_exam.py，
# 此處不重複定義以避免 AmbiguousStep 衝突。

def _start_exam_for_pomodoro(context, email, exam_id):
    """番茄鐘內部使用的開始測驗邏輯。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    exam_key = f"exam_id_{exam_id}"
    exam_uuid = context.ids.get(exam_key, str(exam_id))
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/exams/{exam_uuid}/start",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_exam_id"] = exam_id
    context.memo["current_user_email"] = email


@when('番茄專注時段結束')
def step_impl_focus_ended(context):
    """觸發番茄專注時段結束事件。"""
    exam_id = context.memo.get("current_exam_id", 1)
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/pomodoro/session-complete",
        json={"exam_id": str(exam_id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('第 {n:d} 個專注時段結束')
def step_impl_nth_focus_ended(context, n):
    """觸發第 N 個番茄專注時段結束。"""
    context.memo["pomodoro_session_count"] = n
    step_impl_focus_ended(context)


@when('使用者點擊「繼續作答」')
def step_impl_skip_break(context):
    """使用者跳過休息，繼續作答。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/pomodoro/skip-break",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者點擊「開始休息」')
def step_impl_start_break(context):
    """使用者開始休息。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/pomodoro/start-break",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者完成第 {n:d} 個番茄鐘')
def step_impl_complete_nth_pomodoro(context, n):
    """使用者完成第 N 個番茄鐘。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/pomodoro/session-complete",
        json={"session_number": n},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者查看測驗結果')
def step_impl_view_exam_results(context):
    """查看測驗結果頁。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    exam_id = context.memo.get("current_exam_id", 1)
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    exam_key = f"exam_id_{exam_id}"
    exam_uuid = context.ids.get(exam_key, str(exam_id))
    response = context.api_client.get(
        f"/api/v1/exams/{exam_uuid}/results",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者查看個人儀表板')
def step_impl_view_dashboard(context):
    """查看個人儀表板。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('休息畫面顯示')
def step_impl_break_screen(context):
    """觸發休息畫面顯示。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": ""})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/pomodoro/break-screen",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者作答題目')
def step_impl_answer_question(context):
    """使用者作答題目（通用步驟）。"""
    context.memo["action"] = "answering_question"
    # Just set memo — actual answer submission is handled by specific steps
