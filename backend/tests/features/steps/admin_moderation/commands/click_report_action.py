"""When 管理員點擊檢舉操作按鈕 — Command"""

from behave import when


@when('使用者 "{email}" 於檢舉 "{report_ref}" 點擊「通過」按鈕')
def step_impl_approve_report(context, email, report_ref):
    """呼叫 API 通過（approve）檢舉。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.patch(
        f"/api/v1/admin/reports/{report_ref}/action",
        json={"action": "approve", "note": "通過審核"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 於檢舉 "{report_ref}" 點擊「移除」按鈕')
def step_impl_remove_report(context, email, report_ref):
    """呼叫 API 移除（delete）檢舉標記的內容（第一步，觸發確認）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/reports/{report_ref}/confirm-delete",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["pending_delete_report"] = report_ref
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於內容審核頁面的篩選選單選擇 "{status}"')
def step_impl_filter_reports(context, email, status):
    """呼叫 API 篩選指定狀態的檢舉清單。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/reports?status={status}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["report_filter_status"] = status
    context.memo["admin_token"] = token
