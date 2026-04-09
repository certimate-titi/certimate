"""When 使用者在教練對話框輸入超長訊息 — Command"""

from behave import when


@when('使用者 "{email}" 在節點 {node_id:d} 的教練對話框輸入 {char_count:d} 個字元的訊息')
def step_impl(context, email, node_id, char_count):
    """呼叫 AI 教練 API，輸入指定長度的字元。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    token = context.jwt_helper.create_token(str(user.id))
    long_message = "A" * char_count
    response = context.api_client.post(
        f"/api/v1/knowledge-map/nodes/{node_id}/coach",
        json={"message": long_message},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
