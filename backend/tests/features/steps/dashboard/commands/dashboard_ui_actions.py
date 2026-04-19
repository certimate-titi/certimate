"""When 個人儀表板 UI 互動操作 — Command"""

from behave import when


def _get_token(context, email):
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    return context.jwt_helper.generate_token(str(user.id))


@when('使用者 "{email}" 今日登入並完成一次測驗')
def step_impl_login_and_complete_exam(context, email):
    """呼叫 API 登入並完成測驗（連勝）。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/dashboard/daily-login",
        json={"action": "complete_exam"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 今日首次登入')
def step_impl_first_login_today(context, email):
    """呼叫 API 觸發今日首次登入（微任務生成）。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/dashboard/daily-login",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 首次成功上傳一份資源')
def step_impl_first_upload(context, email):
    """呼叫 API 觸發首次上傳（成就徽章）。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/resources/first-upload",
        json={"filename": "test.pdf", "type": "pdf"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 上傳新頭像')
def step_impl_upload_avatar(context, email):
    """呼叫 API 上傳頭像。"""
    import io
    token = _get_token(context, email)
    files = {"file": ("avatar.png", io.BytesIO(b"fakepng"), "image/png")}
    response = context.api_client.post(
        "/api/v1/dashboard/profile/avatar",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 在儀表板拖放上傳以下檔案：')
def step_impl_drag_drop_upload(context, email):
    """呼叫 API 拖放上傳檔案。"""
    token = _get_token(context, email)
    files = [{"filename": row["檔名"], "type": row["格式"], "size": row["大小"]}
             for row in context.table]
    response = context.api_client.post(
        "/api/v1/dashboard/upload",
        json={"files": files},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 在儀表板提交 YouTube URL "{url}"')
def step_impl_submit_youtube_url(context, email, url):
    """呼叫 API 提交 YouTube URL 解析。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/dashboard/youtube",
        json={"url": url},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 嘗試上傳圖片進行 Vision OCR')
def step_impl_vision_ocr_upload(context, email):
    """呼叫 API 上傳圖片進行 Vision OCR（權限檢查）。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/dashboard/vision-ocr",
        json={"image_data": "mock_base64_image"},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 重試上傳資源 "{resource_id}"')
def step_impl_retry_upload(context, email, resource_id):
    """呼叫 API 重試失敗的上傳。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        f"/api/v1/resources/{resource_id}/retry",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 查看 "{subject}" 的複習月曆，月份為 "{month}"')
def step_impl_view_review_calendar(context, email, subject, month):
    """呼叫 API 查詢複習月曆。"""
    token = _get_token(context, email)
    import urllib.parse
    subject_encoded = urllib.parse.quote(subject)
    response = context.api_client.get(
        f"/api/v1/dashboard/review-calendar?subject={subject_encoded}&month={month}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 從儀表板新增備考科目：')
def step_impl_add_subject_from_dashboard(context, email):
    """呼叫 API 從儀表板新增備考科目。"""
    token = _get_token(context, email)
    subjects = [{"subject": row["科目"], "exam_date": row["考試日期"]}
                for row in context.table]
    response = context.api_client.post(
        "/api/v1/dashboard/add-subject",
        json={"subjects": subjects},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 查看每日任務列表')
def step_impl_view_daily_quests(context, email):
    """呼叫 API 查詢每日任務列表。"""
    token = _get_token(context, email)
    response = context.api_client.get(
        "/api/v1/dashboard/daily-quests",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 在帳戶頁面上傳新大頭貼：')
def step_impl_upload_avatar_account_page(context, email):
    """呼叫 API 從帳戶頁面上傳大頭貼。"""
    import io
    token = _get_token(context, email)
    first_row = context.table[0] if context.table else {}
    filename = first_row.get("檔名", "avatar.png")
    mime = f"image/{first_row.get('格式', 'png').lower()}"
    response = context.api_client.post(
        "/api/v1/dashboard/profile/avatar",
        files={"file": (filename, io.BytesIO(b"fakepng"), mime)},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token


@when('使用者 "{email}" 在帳戶頁面升級訂閱方案至 "{plan}"')
def step_impl_upgrade_subscription(context, email, plan):
    """呼叫 API 升級訂閱方案。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/subscriptions/upgrade",
        json={"plan": plan},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["target_email"] = email


@when('使用者 "{email}" 在帳戶頁面取消訂閱')
def step_impl_cancel_subscription(context, email):
    """呼叫 API 取消訂閱。"""
    token = _get_token(context, email)
    response = context.api_client.post(
        "/api/v1/subscriptions/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["target_email"] = email


@when('使用者 "{email}" 更新通知偏好設定：')
def step_impl_update_notification_prefs(context, email):
    """呼叫 API 更新通知偏好設定。"""
    token = _get_token(context, email)
    prefs = {row["設定項目"]: row["值"] for row in context.table}
    response = context.api_client.put(
        "/api/v1/account/preferences/notifications",
        json=prefs,
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["target_email"] = email
    context.memo["notification_prefs"] = prefs


@when('使用者 "{email}" 切換深色模式為 "{mode}"')
def step_impl_toggle_dark_mode(context, email, mode):
    """呼叫 API 切換深色模式設定。"""
    token = _get_token(context, email)
    response = context.api_client.put(
        "/api/v1/account/preferences/dark-mode",
        json={"dark_mode": mode},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["target_email"] = email
    context.memo["dark_mode"] = mode


@when('使用者 "{email}" 提交刪除帳號請求，確認文字為 "{confirm_text}"')
def step_impl_delete_account(context, email, confirm_text):
    """呼叫 API 刪除帳號（含確認文字）。"""
    token = _get_token(context, email)
    # TestClient.delete() 不支援 json 參數，改用 request()
    response = context.api_client.request(
        "DELETE",
        "/api/v1/account",
        json={"confirm_text": confirm_text},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["target_email"] = email


@when('使用者 "{email}" 在帳戶頁面點擊編輯科目 "{subject}"')
def step_impl_click_edit_subject(context, email, subject):
    """呼叫 API 取得科目編輯頁面（含現有設定）。"""
    token = _get_token(context, email)
    import urllib.parse
    subject_encoded = urllib.parse.quote(subject)
    response = context.api_client.get(
        f"/api/v1/account/subjects/{subject_encoded}/edit",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["edit_subject"] = subject


@when('使用者 "{email}" 在帳戶頁面移除科目 "{subject}"')
def step_impl_remove_subject_from_account(context, email, subject):
    """呼叫 API 從帳戶頁面移除備考科目。"""
    token = _get_token(context, email)
    import urllib.parse
    subject_encoded = urllib.parse.quote(subject)
    response = context.api_client.delete(
        f"/api/v1/account/subjects/{subject_encoded}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["dashboard_token"] = token
    context.memo["target_email"] = email
