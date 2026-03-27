"""Then 回應應為 "1|OK" / "0|..." — Read Model"""

from behave import then


@then('回應應為 "{expected_body}"')
def step_impl(context, expected_body):
    response = context.last_response
    actual = response.text.strip().strip('"')
    assert expected_body in actual, (
        f"預期回應包含 '{expected_body}'，實際: '{actual}'"
    )
