"""When 系統設定頁面 UI 互動操作 — Command"""

from behave import when


@when('使用者 "{email}" 於 AI 模型路由設定頁面選擇方案 "{plan}"，任務類型 "{task_type}"')
def step_impl_select_ai_routing(context, email, plan, task_type):
    """記錄路由設定選擇（UI step，暫存 memo）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["ai_routing_plan"] = plan
    context.memo["ai_routing_task_type"] = task_type
    context.memo["admin_token"] = token
    # Simulate GET to fetch current config (triggers 404 in Red phase)
    response = context.api_client.get(
        f"/api/v1/admin/system-settings/ai-routing?plan={plan}&task_type={task_type}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('將主要模型修改為 "{primary_model}"')
def step_impl_set_primary_model(context, primary_model):
    """記錄主要模型設定。"""
    context.memo["ai_routing_primary_model"] = primary_model


@when('點擊「儲存」按鈕')
def step_impl_click_save(context):
    """執行儲存 AI 模型路由設定。"""
    token = context.memo.get("admin_token")
    plan = context.memo.get("ai_routing_plan")
    task_type = context.memo.get("ai_routing_task_type")
    primary_model = context.memo.get("ai_routing_primary_model")
    if token and plan and primary_model:
        response = context.api_client.put(
            f"/api/v1/admin/system-settings/model-routing/{plan}/{task_type}",
            json={"primary_model": primary_model},
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response


@when('使用者 "{email}" 於方案配額表格中將 "{plan}" 方案的每月上傳數修改為 {count:d}')
def step_impl_edit_quota_table(context, email, plan, count):
    """記錄方案配額修改（UI step）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["quota_plan"] = plan
    context.memo["quota_count"] = count
    context.memo["admin_token"] = token


@when('點擊「儲存變更」按鈕')
def step_impl_click_save_changes(context):
    """執行儲存方案配額變更。"""
    token = context.memo.get("admin_token")
    plan = context.memo.get("quota_plan")
    count = context.memo.get("quota_count")
    if token and plan and count is not None:
        response = context.api_client.put(
            f"/api/v1/admin/system-settings/plan-quota/{plan}",
            json={"monthly_uploads": count},
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response


@when('使用者 "{email}" 於 Feature Flag 列表中將 "{flag_key}" 的開關切換為啟用')
def step_impl_toggle_feature_flag(context, email, flag_key):
    """呼叫 API 切換 Feature Flag 為啟用。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.put(
        f"/api/v1/admin/system-settings/feature-flags/{flag_key}",
        json={"enabled": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於系統設定頁面查看管理員帳號列表')
def step_impl_view_admin_list(context, email):
    """呼叫 API 查詢管理員帳號清單。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/system-settings/admins",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於稽核日誌頁面點擊「匯出 CSV」按鈕')
def step_impl_export_audit_csv(context, email):
    """呼叫 API 匯出稽核日誌 CSV。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/system-settings/audit-logs/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 於稽核日誌頁面設定起始日期為 "{start_date}"，結束日期為 "{end_date}"')
def step_impl_set_audit_date_range(context, email, start_date, end_date):
    """記錄稽核日誌日期範圍（UI step）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    context.memo["audit_start_date"] = start_date
    context.memo["audit_end_date"] = end_date
    context.memo["admin_token"] = token


@when('點擊「篩選」按鈕')
def step_impl_click_filter(context):
    """執行稽核日誌日期篩選。"""
    token = context.memo.get("admin_token")
    start = context.memo.get("audit_start_date")
    end = context.memo.get("audit_end_date")
    if token and start and end:
        response = context.api_client.get(
            f"/api/v1/admin/system-settings/audit-logs?start={start}&end={end}",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response


@when('使用者 "{email}" 於稽核日誌頁面查看紀錄列表')
def step_impl_view_audit_log_list(context, email):
    """呼叫 API 查詢稽核日誌（含分頁）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/admin/system-settings/audit-logs?page=1&per_page=50",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["audit_current_page"] = 1


@when('點擊「下一頁」按鈕')
def step_impl_next_page(context):
    """切換至下一頁稽核日誌。"""
    token = context.memo.get("admin_token")
    current_page = context.memo.get("audit_current_page", 1)
    next_page = current_page + 1
    if token:
        response = context.api_client.get(
            f"/api/v1/admin/system-settings/audit-logs?page={next_page}&per_page=50",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
        context.memo["audit_current_page"] = next_page
