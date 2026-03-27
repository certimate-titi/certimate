"""Then step: 週報數據僅與使用者自己的歷史比較，不含排名"""

from behave import then


@then('週報數據僅與使用者自己的歷史比較，不含排名')
def step_impl(context):
    data = context.last_response.json()
    reports = data.get("reports", [])

    for report in reports:
        assert "ranking" not in report, f"Report contains ranking: {report}"
        assert "rank" not in report, f"Report contains rank: {report}"
