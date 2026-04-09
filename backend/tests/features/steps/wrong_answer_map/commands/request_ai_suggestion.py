"""When 使用者 "{email}" 請求 AI 學習建議."""

from behave import when


@when('使用者 "{email}" 請求 AI 學習建議')
def step_impl(context, email):
    """呼叫 AI 學習建議 API。"""
    user = None
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    subject_id = context.memo.get("subject_id")
    assert subject_id, "subject_id 未設定，請先執行 Given 步驟"

    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/wrong-answer-map/subjects/{subject_id}/ai-suggestions",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
