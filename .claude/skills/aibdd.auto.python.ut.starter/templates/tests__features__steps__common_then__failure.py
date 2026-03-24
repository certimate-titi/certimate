from behave import then


@then('操作失敗')
def step_impl(context):
    """驗證前一個操作執行失敗。"""
    assert context.last_error is not None, \
        "預期操作失敗，但操作成功了"
