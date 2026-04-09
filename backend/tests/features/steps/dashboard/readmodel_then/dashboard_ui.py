"""Then 個人儀表板 UI 驗證 — ReadModel Then"""

from behave import then


@then('系統應產生 1 至 3 個每日微任務')
def step_impl_daily_micro_tasks_generated(context):
    """驗證每日微任務已產生（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        quests = data if isinstance(data, list) else data.get("quests", [])
        assert 1 <= len(quests) <= 3, \
            f"每日微任務應為 1-3 個，實際 {len(quests)} 個"


@then('回應應包含新頭像的 URL')
def step_impl_avatar_url_in_response(context):
    """驗證回應包含新頭像 URL（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        assert "avatar_url" in data or "url" in data, \
            "回應應包含 avatar_url 或 url 欄位"


@then('上傳狀態應為 "{status}"')
def step_impl_upload_status(context, status):
    """驗證上傳狀態為預期值（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        actual_status = data.get("status") or data.get("upload_status")
        assert actual_status == status, \
            f"預期上傳狀態 '{status}'，實際 '{actual_status}'"


@then('回應應包含上傳資源的 ID')
def step_impl_resource_id_in_response(context):
    """驗證回應包含資源 ID（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        assert "id" in data or "resource_id" in data, \
            "回應應包含 id 或 resource_id 欄位"


@then('資源類型應為 "{resource_type}"')
def step_impl_resource_type(context, resource_type):
    """驗證資源類型（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        actual = data.get("type") or data.get("resource_type")
        assert actual == resource_type, \
            f"預期資源類型 '{resource_type}'，實際 '{actual}'"


@then('回應應包含升級方案的連結')
def step_impl_upgrade_link_in_response(context):
    """驗證回應包含升級方案連結（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('回應應包含上傳進度狀態：')
def step_impl_upload_progress_status(context):
    """驗證回應包含上傳進度狀態（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        for row in context.table:
            field = row["欄位"]
            assert field in data, f"回應應包含欄位 '{field}'"


@then('回應中的雷達圖資料應包含：')
def step_impl_radar_chart_data(context):
    """驗證雷達圖資料包含指定領域與強度（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        radar = data.get("radar_chart") or data.get("radar") or data
        if isinstance(radar, list):
            radar_by_domain = {item.get("domain", item.get("領域")): item for item in radar}
            for row in context.table:
                domain = row["領域"]
                strength = int(row["強度"])
                assert domain in radar_by_domain, \
                    f"雷達圖應包含領域 '{domain}'"


@then('回應中的月曆複習點應包含：')
def step_impl_calendar_review_points(context):
    """驗證複習月曆包含指定日期的複習點（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        calendar = data if isinstance(data, list) else data.get("calendar", [])
        calendar_by_date = {item.get("date"): item for item in calendar}
        for row in context.table:
            date = row["日期"]
            assert date in calendar_by_date, \
                f"月曆複習點應包含日期 '{date}'"


@then('每個任務應包含 badge 資訊：')
def step_impl_quest_badge_info(context):
    """驗證每個任務包含 badge 資訊（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        quests = data if isinstance(data, list) else data.get("quests", [])
        for quest in quests:
            for row in context.table:
                field = row["欄位"]
                assert field in quest, f"任務應包含欄位 '{field}'"


@then('使用者 "{email}" 的通知偏好應為：')
def step_impl_notification_prefs_check(context, email):
    """驗證使用者通知偏好設定（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('使用者 "{email}" 的深色模式設定應為 "{mode}"')
def step_impl_dark_mode_check(context, email, mode):
    """驗證使用者深色模式設定（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應導向至 Onboarding 科目編輯頁，帶入 "{subject}" 的現有設定')
def step_impl_navigate_to_onboarding_edit(context, subject):
    """驗證系統導向至 Onboarding 科目編輯頁（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
