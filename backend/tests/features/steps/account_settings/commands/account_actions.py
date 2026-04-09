"""When 帳號設定操作命令 — Commands"""

from behave import when


@when('使用者 "{email}" 變更密碼：')
def step_impl_change_password(context, email):
    """呼叫 API 變更密碼。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))

    payload = {}
    for row in context.table:
        payload[row["欄位"]] = row["值"]

    response = context.api_client.post(
        "/api/v1/account/change-password",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 查詢使用量')
def step_impl_query_usage(context, email):
    """呼叫 API 查詢使用量。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/account/usage",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 申請刪除帳號並輸入確認文字 "{confirm_text}"')
def step_impl_delete_account(context, email, confirm_text):
    """呼叫 API 申請刪除帳號。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    context.memo["delete_target_user_id"] = str(user.id)
    token = context.jwt_helper.generate_token(str(user.id))
    # TestClient.delete() 不支援 json 參數，改用 request
    import httpx
    response = context.api_client.request(
        "DELETE",
        "/api/v1/account",
        json={"confirm_text": confirm_text},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 更新通知偏好：')
def step_impl_update_notification_pref(context, email):
    """呼叫 API 更新通知偏好設定。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))

    payload = {}
    for row in context.table:
        val = row["值"]
        if val.lower() == "true":
            val = True
        elif val.lower() == "false":
            val = False
        payload[row["欄位"]] = val

    response = context.api_client.patch(
        "/api/v1/account/notification-preferences",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
