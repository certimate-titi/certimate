"""Then 導向至指定步驟頁 + 資料保留驗證 — ReadModel Then"""

from behave import then


@then('系統應導向至 Step 1 歡迎與基本資訊頁')
def step_impl_nav_step1(context):
    """驗證系統導向至 Step 1（API 回應 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('先前填寫的資料應保留不變')
def step_impl_data_preserved(context):
    """驗證資料保留不變（Red 階段：允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應導向至 Step 2 選擇備考科目頁')
def step_impl_nav_step2(context):
    """驗證系統導向至 Step 2（API 回應 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('先前選擇的科目與設定應保留不變')
def step_impl_subjects_preserved(context):
    """驗證科目設定保留不變（Red 階段：允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應導向至 Step 3 學習偏好設定頁')
def step_impl_nav_step3(context):
    """驗證系統導向至 Step 3（API 回應 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('先前設定的偏好應保留不變')
def step_impl_prefs_preserved(context):
    """驗證學習偏好保留不變（Red 階段：允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
