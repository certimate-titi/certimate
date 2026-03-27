"""Then 回應應包含機構名稱 — ReadModel Then"""

from behave import then


@then('回應應包含機構名稱 "{expected_name}"')
def step_impl(context, expected_name):
    response = context.last_response
    data = response.json()

    actual = data.get("institution_name", "")
    assert expected_name in actual, \
        f"預期機構名稱包含 '{expected_name}'，實際 '{actual}'"
