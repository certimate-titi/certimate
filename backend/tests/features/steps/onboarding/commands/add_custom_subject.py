"""When 使用者在自訂科目輸入欄輸入名稱並點擊新增 — Command"""

from behave import when


@when('使用者在自訂科目輸入欄輸入 "{subject_name}" 並點擊新增')
def step_impl(context, subject_name):
    """呼叫 API 新增自訂備考科目。"""
    token = context.memo.get("current_token")
    response = context.api_client.post(
        "/api/v1/onboarding/subjects/custom",
        json={"subject_name": subject_name, "is_custom": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["last_custom_subject"] = subject_name
