"""Then 學習模式應為 — ReadModel Then"""

from behave import then


@then('學習模式應為 "{expected_mode}"')
def step_impl(context, expected_mode):
    response = context.last_response
    data = response.json()

    actual = data.get("learning_mode", "")
    assert actual == expected_mode, \
        f"預期學習模式 '{expected_mode}'，實際 '{actual}'"
