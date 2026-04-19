"""When 管理員後台 UI 互動操作 — Command"""

from behave import when


def _resolve_target_user_uuid(context, user_seq_id: int) -> str:
    """將 Background table 序號轉成真實 UUID。"""
    from app.models.user import User
    all_users = context.db_session.query(User).order_by(User.created_at).all()
    if user_seq_id <= len(all_users):
        return str(all_users[user_seq_id - 1].id)
    return str(user_seq_id)


@when('使用者 "{email}" 於用戶管理頁面點擊「匯出 CSV」按鈕')
def step_impl_click_export_csv(context, email):
    """呼叫 API 匯出使用者 CSV。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/users/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於用戶管理頁面點擊「新增使用者」按鈕')
def step_impl_click_add_user(context, email):
    """記錄新增使用者動作（UI step，暫存 memo）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["admin_token"] = token
    # Simulate GET to trigger 404 in Red phase
    response = context.api_client.get(
        "/api/v1/admin/users/create-dialog",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('在彈出的對話框中輸入 Email 為 "{new_email}"，密碼為 "{password}"')
def step_impl_input_new_user_credentials(context, new_email, password):
    """呼叫 API 新增使用者（POST）。"""
    token = context.memo.get("admin_token")
    assert token, "未取得 admin_token"
    response = context.api_client.post(
        "/api/v1/admin/users",
        json={"email": new_email, "password": password},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["new_user_email"] = new_email


@when('使用者 "{email}" 於使用者 {user_id:d} 的操作選單點擊「發送通知」')
def step_impl_click_notify_user(context, email, user_id):
    """記錄發送通知動作（UI step，暫存 memo）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["admin_token"] = token
    # 從 Background table 的序號找到目標用戶的真實 UUID
    all_users = context.db_session.query(User).order_by(User.created_at).all()
    target_user = all_users[user_id - 1] if user_id <= len(all_users) else None
    target_uuid = str(target_user.id) if target_user else str(user_id)
    context.memo["target_user_id"] = target_uuid


@when('在通知輸入框中輸入訊息 "{message}"')
def step_impl_input_notification_message(context, message):
    """記錄通知訊息（UI step，暫存 memo）。"""
    context.memo["notification_message"] = message


@when('點擊「送出」按鈕')
def step_impl_click_submit(context):
    """執行發送通知。"""
    token = context.memo.get("admin_token")
    user_id = context.memo.get("target_user_id")
    message = context.memo.get("notification_message", "")
    if token and user_id:
        response = context.api_client.post(
            f"/api/v1/admin/users/{user_id}/notify",
            json={"message": message},
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response


@when('使用者 "{email}" 停權使用者 {user_id:d}，原因為 "{reason}"')
def step_impl_suspend_user_direct(context, email, user_id, reason):
    """直接呼叫停權 API（含自動通知信）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    target_uuid = _resolve_target_user_uuid(context, user_id)
    response = context.api_client.post(
        "/api/v1/admin/users/suspend",
        json={"target_user_id": target_uuid, "reason": reason},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response



@when('使用者 "{email}" 於使用者 {user_id:d} 的操作選單點擊「停權」')
def step_impl_click_suspend_user(context, email, user_id):
    """記錄停權動作（UI step，暫存 memo）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["admin_token"] = token
    context.memo["target_user_id"] = _resolve_target_user_uuid(context, user_id)


@when('輸入停權原因為 "{reason}" 並點擊「確認」')
def step_impl_input_suspend_reason(context, reason):
    """呼叫 API 執行停權操作。"""
    token = context.memo.get("admin_token")
    user_id = context.memo.get("target_user_id")
    assert token, "未取得 admin_token"
    assert user_id, "未取得 target_user_id"
    response = context.api_client.post(
        "/api/v1/admin/users/suspend",
        json={"target_user_id": user_id, "reason": reason},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 於使用者 {user_id:d} 的操作選單點擊「刪除帳號」')
def step_impl_click_delete_user(context, email, user_id):
    """記錄刪除帳號動作（UI step，暫存 memo）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["admin_token"] = token
    context.memo["target_user_id"] = _resolve_target_user_uuid(context, user_id)


@when('輸入確認名稱為 "{name}" 並點擊「確認刪除」')
def step_impl_input_confirm_delete(context, name):
    """呼叫 API 執行刪除帳號。"""
    token = context.memo.get("admin_token")
    user_id = context.memo.get("target_user_id")
    assert token, "未取得 admin_token"
    assert user_id, "未取得 target_user_id"
    response = context.api_client.post(
        "/api/v1/admin/users/delete",
        json={"target_user_id": user_id, "confirm_name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 於使用者 {user_id:d} 的操作選單點擊「調整訂閱」')
def step_impl_click_adjust_subscription(context, email, user_id):
    """記錄調整訂閱動作（UI step，暫存 memo）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["admin_token"] = token
    context.memo["target_user_id"] = _resolve_target_user_uuid(context, user_id)


@when('在 Modal 中選擇方案為 "{plan}"，起始日期為 "{start_date}"，結束日期為 "{end_date}"')
def step_impl_select_subscription_plan(context, plan, start_date, end_date):
    """記錄調整訂閱參數（UI step，暫存 memo）。"""
    context.memo["subscription_plan"] = plan
    context.memo["subscription_start_date"] = start_date
    context.memo["subscription_end_date"] = end_date


@when('點擊「確認調整」按鈕')
def step_impl_click_confirm_adjust(context):
    """呼叫 API 執行訂閱調整。"""
    token = context.memo.get("admin_token")
    user_id = context.memo.get("target_user_id")
    plan = context.memo.get("subscription_plan")
    start_date = context.memo.get("subscription_start_date")
    end_date = context.memo.get("subscription_end_date")
    if token and user_id and plan:
        response = context.api_client.post(
            f"/api/v1/admin/users/{user_id}/adjust-subscription",
            json={"plan": plan, "start_date": start_date, "end_date": end_date},
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response


@when('使用者 "{email}" 於用戶管理頁面的搜尋框輸入 "{keyword}"')
def step_impl_search_user_by_keyword(context, email, keyword):
    """呼叫 API 以關鍵字搜尋使用者。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/users?keyword={keyword}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["search_keyword"] = keyword


@when('使用者 "{email}" 於用戶管理頁面查看用戶列表')
def step_impl_view_user_list(context, email):
    """呼叫 API 查詢使用者列表（含分頁）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/users?page=1&per_page=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["user_list_current_page"] = 1


@when('點擊「上一頁」按鈕')
def step_impl_prev_page(context):
    """切換至上一頁使用者列表。"""
    token = context.memo.get("admin_token")
    current_page = context.memo.get("user_list_current_page") or \
        context.memo.get("audit_current_page", 2)
    prev_page = max(1, current_page - 1)
    if token:
        response = context.api_client.get(
            f"/api/v1/admin/users?page={prev_page}&per_page=20",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
        context.memo["user_list_current_page"] = prev_page
