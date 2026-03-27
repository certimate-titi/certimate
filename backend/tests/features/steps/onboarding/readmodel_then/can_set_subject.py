"""Then 使用者可選擇新科目並設定考試日期與自評程度 — ReadModel Then"""

from behave import then


@then('使用者可選擇新科目並設定考試日期與自評程度')
def step_impl(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text}"
