"""Common Then — 操作失敗狀態碼為 N / 錯誤訊息應包含「X」."""

from behave import then


@then('操作失敗狀態碼為 {code:d}')
def status_code_no_comma(context, code):
    assert context.last_response is not None, "無 last_response"
    actual = context.last_response.status_code
    assert actual == code, f"預期狀態碼 {code}，實際 {actual}: {context.last_response.text}"


@then('錯誤訊息應包含「{text}」')
def error_message_brackets(context, text):
    assert context.last_response is not None, "無 last_response"
    body = context.last_response.text
    assert text in body, f"錯誤訊息不含「{text}」：{body}"
