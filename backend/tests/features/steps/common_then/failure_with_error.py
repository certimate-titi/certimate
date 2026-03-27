from behave import then


@then('操作失敗，錯誤為「{message}」')
def step_impl(context, message):
    response = context.last_response
    assert 400 <= response.status_code < 500, \
        f"預期失敗（4XX），實際 {response.status_code}: {response.text}"

    data = response.json()

    # FastAPI HTTPException 用 detail，可能是 str 或 dict
    detail = data.get("detail", data)
    if isinstance(detail, dict):
        actual_message = detail.get("message") or str(detail)
    elif isinstance(detail, str):
        actual_message = detail
    else:
        actual_message = str(detail)

    assert message in str(actual_message), \
        f"預期錯誤訊息包含 '{message}'，實際為 '{actual_message}'"
