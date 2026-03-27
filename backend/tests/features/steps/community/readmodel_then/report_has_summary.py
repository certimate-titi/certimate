"""Then step: 週報應包含 AI 生成的進步摘要（非空白）"""

from behave import then


@then('週報應包含 AI 生成的進步摘要（非空白）')
def step_impl(context):
    data = context.last_response.json()
    reports = data.get("reports", [])
    assert len(reports) > 0, "No reports generated"

    for report in reports:
        summary = report.get("progress_summary", "")
        assert summary and summary.strip(), \
            f"Expected non-empty progress_summary, got: '{summary}'"
