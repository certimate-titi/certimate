"""When B2B 機構管理後台 UI 互動操作 — Command"""

from behave import when


@when('使用者 "{email}" 查看學員 {student_id:d} 的複習排程')
def step_impl_view_schedule(context, email, student_id):
    """呼叫 API 查看學員複習排程。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    target_id = context.ids.get(str(student_id), str(student_id))
    response = context.api_client.get(
        f"/api/v1/b2b/students/{target_id}/review-schedule",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 以關鍵字 "{keyword}" 搜尋機構 {inst_id:d} 的學員列表')
def step_impl_search_students(context, email, keyword, inst_id):
    """呼叫 API 以關鍵字搜尋機構學員。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/b2b/institutions/{inst_id}/students?search={keyword}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["search_keyword"] = keyword


@when('使用者 "{email}" 展開學員 {student_id:d} 的能力表')
def step_impl_expand_competency(context, email, student_id):
    """呼叫 API 取得學員能力表（CompetencyBar 資料）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    target_id = context.ids.get(str(student_id), str(student_id))
    response = context.api_client.get(
        f"/api/v1/b2b/students/{target_id}/competency",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token
    context.memo["student_id"] = student_id


@when('使用者 "{email}" 查看群組 {group_id:d} 的班級弱點分析')
def step_impl_view_weakness_analysis(context, email, group_id):
    """呼叫 API 查看班級弱點分析。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/b2b/groups/{group_id}/weakness-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["admin_token"] = token


@when('使用者 "{email}" 在機構管理後台點擊「匯入學生名單」按鈕')
def step_impl_click_import_students(context, email):
    """呼叫 API 觸發匯入學生名單（placeholder）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/b2b/import-students/placeholder",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 在機構管理後台點擊快速操作卡片')
def step_impl_click_quick_action(context, email):
    """呼叫 API 觸發快速操作（placeholder）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/b2b/quick-actions/placeholder",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 在班級分析頁點擊「匯出詳細報告」按鈕')
def step_impl_click_export_report(context, email):
    """呼叫 API 觸發匯出詳細報告（placeholder）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/b2b/class-analysis/export-placeholder",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
