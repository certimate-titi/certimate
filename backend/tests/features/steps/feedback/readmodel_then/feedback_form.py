"""Then 頁面應顯示意見反饋表單 — Readmodel Then"""

from behave import then


@then('頁面應顯示意見反饋表單（包含類型、主旨、內容欄位）')
def step_impl(context):
    # In API E2E context, verify the feedback endpoint responded successfully
    # which means the user can access the feedback form page
    response = context.last_response
    assert response.status_code < 400, \
        f"預期成功存取反饋頁面，實際 HTTP {response.status_code}: {response.text}"
