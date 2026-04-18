"""When 管理員點擊檢舉操作按鈕 — Command"""

from behave import when


@when('使用者 "{email}" 於檢舉 "{report_ref}" 點擊「通過」按鈕')
def step_impl_approve_report(context, email, report_ref):
    """呼叫 /admin/moderation/{item_id}/approve 通過檢舉。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/admin/moderation/{report_ref}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於檢舉 "{report_ref}" 點擊「移除」按鈕')
def step_impl_remove_report(context, email, report_ref):
    """點擊「移除」後顯示確認對話框（純 UI 狀態，不呼叫後端）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    context.memo["pending_delete_report"] = report_ref
    context.memo["admin_token"] = token
    context.memo["confirm_dialog_shown"] = True
    context.last_response = type(
        "FakeResp", (), {
            "status_code": 200,
            "json": lambda self: {"confirm_required": True, "report_ref": report_ref},
            "text": "confirm dialog",
        },
    )()


@when('使用者 "{email}" 於內容審核頁面的篩選選單選擇 "{status}"')
def step_impl_filter_reports(context, email, status):
    """呼叫 /admin/moderation/reports 篩選指定狀態。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/admin/moderation/reports?status={status}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["report_filter_status"] = status
    context.memo["admin_token"] = token
