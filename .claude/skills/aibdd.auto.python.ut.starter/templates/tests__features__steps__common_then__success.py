from behave import then


@then('操作成功')
def step_impl(context):
    """驗證前一個操作執行成功。"""
    assert context.last_error is None, \
        f"預期操作成功，但發生錯誤: {context.last_error}"
