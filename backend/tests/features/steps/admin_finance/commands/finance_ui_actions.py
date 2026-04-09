"""When 財務管理頁面 UI 互動操作 — Command"""

from behave import when


@when('使用者 "{email}" 於財務管理頁面點擊「匯出報告」按鈕')
def step_impl_export_report(context, email):
    """呼叫 API 匯出財務報告。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/finance/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於交易紀錄頁面的搜尋框輸入 "{keyword}"')
def step_impl_search_transaction(context, email, keyword):
    """呼叫 API 搜尋交易紀錄。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/finance/transactions?search={keyword}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["search_keyword"] = keyword


@when('使用者 "{email}" 於交易紀錄頁面的狀態篩選下拉選單選擇 "{status}"')
def step_impl_filter_transaction_status(context, email, status):
    """呼叫 API 依狀態篩選交易紀錄。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/finance/transactions?status={status}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["filter_status"] = status


@when('使用者 "{email}" 於交易紀錄頁面點擊交易 "{transaction_id}" 的展開按鈕')
def step_impl_expand_transaction(context, email, transaction_id):
    """呼叫 API 取得交易詳情。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/finance/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["expanded_transaction_id"] = transaction_id


@when('使用者 "{email}" 於財務管理頁面查看 MRR 趨勢圖表')
def step_impl_view_mrr_chart(context, email):
    """呼叫 API 查詢 MRR 趨勢資料。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/finance/mrr-trend",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
