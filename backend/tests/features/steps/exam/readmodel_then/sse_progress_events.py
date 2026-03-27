"""Then SSE 應依序推送以下進度事件 — ReadModel Then"""

from behave import then


@then('SSE 應依序推送以下進度事件：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    events = data.get("progress_events", [])

    for row in context.table:
        expected_pct = int(row["進度百分比"])
        expected_msg = row["說明訊息"]
        expected_stage = row.get("階段", None)

        found = False
        for event in events:
            if event.get("percentage") == expected_pct:
                found = True
                assert event.get("message") == expected_msg, (
                    f"進度 {expected_pct}% 的訊息應為 '{expected_msg}'，"
                    f"但得到 '{event.get('message')}'"
                )
                if expected_stage:
                    assert event.get("stage") == expected_stage, (
                        f"進度 {expected_pct}% 的階段應為 '{expected_stage}'，"
                        f"但得到 '{event.get('stage')}'"
                    )
                break

        assert found, f"找不到進度 {expected_pct}% 的事件"
