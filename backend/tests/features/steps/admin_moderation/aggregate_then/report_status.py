"""Then 檢舉的狀態應為 — Aggregate Then"""

from behave import then

from app.models.content_report import ContentReport


@then('檢舉 "{report_ref}" 的狀態應為 "{expected_status}"')
def step_impl(context, report_ref, expected_status):
    db = context.db_session
    db.expire_all()

    report = db.query(ContentReport).filter(
        ContentReport.report_ref == report_ref
    ).first()

    assert report is not None, f"找不到檢舉 {report_ref}"
    assert report.status == expected_status, \
        f"檢舉 {report_ref} 的狀態應為 '{expected_status}'，實際 '{report.status}'"
