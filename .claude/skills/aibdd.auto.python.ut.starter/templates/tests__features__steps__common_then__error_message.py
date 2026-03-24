from behave import then


@then('錯誤訊息應為 "{message}"')
def step_impl(context, message):
    """驗證錯誤訊息。"""
    error = context.last_error
    assert error is not None, "預期操作失敗，但沒有發生錯誤"
    assert message in str(error), \
        f"預期錯誤訊息包含 '{message}'，實際為 '{str(error)}'"
