"""Then — 操作成功（不阻斷使用者）。"""

from behave import then


@then('操作成功（不阻斷使用者）')
def step_success_no_block(context):
    response = context.last_response
    assert response.status_code in [200, 201, 204], \
        f"預期成功（2XX），實際 {response.status_code}: {response.text}"
