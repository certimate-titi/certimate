"""When 測驗結果頁面 UI 互動操作 — Command"""

from behave import when


@when('使用者 "{email}" 點擊分享到 LinkedIn 按鈕')
def step_impl_click_linkedin(context, email):
    """呼叫 API 觸發 LinkedIn 分享（placeholder 功能）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/exam-results/share/linkedin",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 點擊下載成績卡片按鈕')
def step_impl_click_download_card(context, email):
    """呼叫 API 觸發成績卡片下載（placeholder 功能）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/exam-results/score-card/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 點擊 AI 教練介入卡片上的「前往錯題複習」按鈕')
def step_impl_go_to_wrong_review(context, email):
    """呼叫 API 取得錯題複習跳轉資訊。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        return
    token = context.jwt_helper.create_token(str(user.id))
    exam_id = context.memo.get("low_accuracy_exam_id", 0)
    response = context.api_client.get(
        f"/api/v1/exam-results/{exam_id}/wrong-review-redirect",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
