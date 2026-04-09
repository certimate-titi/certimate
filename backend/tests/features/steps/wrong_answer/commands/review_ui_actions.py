"""When 錯題複習頁面 UI 互動操作 — Command"""

from behave import when


@when('使用者在側邊列表點擊題目 {question_id:d}')
def step_impl_click_sidebar_question(context, question_id):
    """呼叫 API 切換顯示指定題目的解析。"""
    token = context.memo.get("current_token")
    exam_id = context.memo.get("review_exam_id", 1)
    if not token:
        email = context.memo.get("review_email", "")
        if email:
            from app.models.user import User
            user = context.db_session.query(User).filter(User.email == email).first()
            if user:
                token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/wrong-answers/exams/{exam_id}/questions/{question_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["selected_question_id"] = question_id


@when('使用者點擊「查看引用來源」切換按鈕')
def step_impl_expand_citations(context):
    """呼叫 API 取得引用來源（展開）。"""
    token = context.memo.get("current_token")
    exam_id = context.memo.get("wrong_analysis_exam_id", 3)
    if token:
        response = context.api_client.get(
            f"/api/v1/wrong-answers/exams/{exam_id}/source-citations",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
        context.memo["citations_expanded"] = True


@when('使用者再次點擊「收合引用來源」')
def step_impl_collapse_citations(context):
    """模擬收合引用來源（UI 操作，回應保持 200/404）。"""
    context.memo["citations_expanded"] = False


@when('使用者 "{email}" 在錯題複習頁面嘗試開啟 AI 教練聊天')
def step_impl_try_open_coach(context, email):
    """呼叫 API 嘗試開啟 AI 教練（可能因額度用完被拒）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/ai-coach/session",
        json={"context": "wrong_review"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_token"] = token


@when('使用者 "{email}" 進入錯題複習頁面')
def step_impl_enter_review_page(context, email):
    """呼叫 API 查詢錯題記錄列表。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/wrong-answers",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_token"] = token


@when('使用者點擊「回到儀表板」連結')
def step_impl_click_dashboard_link(context):
    """模擬點擊回到儀表板（Red 階段保留現有 response）。"""
    pass  # UI navigation; response stays as-is for Red phase
