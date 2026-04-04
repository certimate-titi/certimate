"""Then 系統應建立測驗任務，包含題型 (@ignore) — ReadModel Then"""

from behave import then, use_step_matcher

use_step_matcher("re")


@then('系統應建立測驗任務，包含題型 (?P<types>.+)')
def step_impl(context, types):
    response = context.last_response
    data = response.json()

    # Parse expected types: "單選" 和 "多選" 和 "填空"
    expected_types = [t.strip().strip('"') for t in types.split("和")]

    actual_types = data.get("question_types", [])
    for t in expected_types:
        assert t in actual_types, (
            f"測驗應包含題型 '{t}'，但得到 {actual_types}"
        )


use_step_matcher("parse")
