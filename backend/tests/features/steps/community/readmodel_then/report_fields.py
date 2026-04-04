"""Then step: 每份週報應包含："""

from behave import then


@then('每份週報應包含：')
def step_impl(context):
    data = context.last_response.json()
    reports = data.get("reports", [])
    assert len(reports) > 0, "No reports to validate"

    required_fields = [row["欄位"].strip() for row in context.table]

    for i, report in enumerate(reports):
        for field in required_fields:
            assert field in report, \
                f"Report #{i} missing field '{field}'. Report: {report}"
