"""Then step: AI 教練的訊息應包含："""

from behave import then


@then('AI 教練的訊息應包含：')
def step_impl(context):
    data = context.last_response.json()
    message = data.get("message", {})

    for row in context.table:
        content_type = row["內容類型"]
        assert content_type in message, \
            f"Message missing content type '{content_type}'. Message: {message}"
        value = message[content_type]
        assert value and len(value.strip()) > 0, \
            f"Content for '{content_type}' is empty"
