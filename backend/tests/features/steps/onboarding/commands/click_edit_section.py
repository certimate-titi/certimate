"""When 使用者點擊確認頁各區塊的編輯按鈕 — Command"""

from behave import when


@when('使用者點擊個人資訊區塊的「編輯」按鈕')
def step_impl_edit_profile(context):
    """呼叫 API 取得 Step 1 個人資訊（返回編輯模式）。"""
    token = context.memo.get("current_token")
    response = context.api_client.get(
        "/api/v1/onboarding/step/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["edit_target_step"] = 1


@when('使用者點擊備考科目區塊的「編輯」按鈕')
def step_impl_edit_subjects(context):
    """呼叫 API 取得 Step 2 備考科目（返回編輯模式）。"""
    token = context.memo.get("current_token")
    response = context.api_client.get(
        "/api/v1/onboarding/step/2",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["edit_target_step"] = 2


@when('使用者點擊學習偏好區塊的「編輯」按鈕')
def step_impl_edit_preferences(context):
    """呼叫 API 取得 Step 3 學習偏好（返回編輯模式）。"""
    token = context.memo.get("current_token")
    response = context.api_client.get(
        "/api/v1/onboarding/step/3",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["edit_target_step"] = 3
