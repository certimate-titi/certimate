"""When 錯題複習頁面 UI 互動操作 — Command"""

from behave import when


def _get_token(context, email=None):
    token = context.memo.get("current_token")
    if token:
        return token
    email = email or context.memo.get("review_email")
    if not email:
        return None
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        return None
    token = context.jwt_helper.generate_token(str(user.id))
    context.memo["current_token"] = token
    return token


def _fake_resp(context, status, payload):
    data = payload
    context.last_response = type(
        "FakeResp", (), {
            "status_code": status,
            "json": lambda self: data,
            "text": str(data),
        },
    )()


@when('使用者在側邊列表點擊題目 {question_id:d}')
def step_impl_click_sidebar_question(context, question_id):
    """呼叫 API 取得單題錯題分析。"""
    exam_id = context.memo.get("review_exam_id", 1)
    token = _get_token(context)
    if not token:
        _fake_resp(context, 404, {"message": "no token"})
        return
    exam_uuid = context.ids.get(f"exam_id_{exam_id}", str(exam_id))
    q_uuid = context.ids.get(f"question_id_{question_id}", str(question_id))
    response = context.api_client.get(
        f"/api/v1/wrong-answers/{exam_uuid}/questions/{q_uuid}/analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["selected_question_id"] = question_id


@when('使用者點擊「查看引用來源」切換按鈕')
def step_impl_expand_citations(context):
    """展開引用來源（純前端 UI 狀態，不呼叫後端）。"""
    context.memo["citations_expanded"] = True
    _fake_resp(context, 200, {"citations_expanded": True})


@when('使用者再次點擊「收合引用來源」')
def step_impl_collapse_citations(context):
    """收合引用來源（純前端 UI 狀態）。"""
    context.memo["citations_expanded"] = False
    _fake_resp(context, 200, {"citations_expanded": False})


@when('使用者 "{email}" 在錯題複習頁面嘗試開啟 AI 教練聊天')
def step_impl_try_open_coach(context, email):
    """呼叫 AI 教練 API（額度用完時會被拒）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/ai/coach",
        json={"message": "wrong_review 開啟教練"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_token"] = token


@when('使用者 "{email}" 進入錯題複習頁面')
def step_impl_enter_review_page(context, email):
    """查詢錯題記錄列表。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/wrong-answers",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_token"] = token
    context.memo["review_email"] = email


@when('使用者點擊「回到儀表板」連結')
def step_impl_click_dashboard_link(context):
    """純前端導覽操作，memo 標記即可。"""
    context.memo["navigated_to_dashboard"] = True
