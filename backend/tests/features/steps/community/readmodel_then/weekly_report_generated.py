"""Then step: 系統應為使用者 "{email}" 生成週報，內容包含："""

from behave import then


@then('系統應為使用者 "{email}" 生成週報，內容包含：')
def step_impl(context, email):
    data = context.last_response.json()
    reports = data.get("reports", [])

    # Find the report for this user
    report = None
    for r in reports:
        if r.get("user_email") == email:
            report = r
            break
    assert report is not None, f"No report found for {email}. Reports: {reports}"

    for row in context.table:
        field = row["欄位"].strip()
        expected = row["值"].strip()

        actual = report.get(field)
        assert actual is not None, f"Field '{field}' not found in report: {report}"

        # Compare as float for numeric values
        assert float(actual) == float(expected), \
            f"Field '{field}': expected {expected}, got {actual}"
