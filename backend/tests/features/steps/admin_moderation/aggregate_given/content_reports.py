"""Given 系統中有以下內容檢舉 — Aggregate Given"""

from behave import given

from app.models.content_report import ContentReport, ReportStatus


@given('系統中有以下內容檢舉：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        report_ref = row["檢舉 ID"]
        reporter_id = int(row["檢舉者 ID"])
        report_type = row["類型"]
        target_type = row["目標類型"]
        target_id = int(row["目標 ID"])
        status_raw = row["狀態"]

        status_map = {
            "pending": ReportStatus.PENDING,
            "resolved": ReportStatus.RESOLVED,
            "dismissed": ReportStatus.DISMISSED,
        }

        report = ContentReport(
            report_ref=report_ref,
            reporter_id=reporter_id,
            report_type=report_type,
            target_type=target_type,
            target_id=target_id,
            status=status_map.get(status_raw, ReportStatus.PENDING),
        )
        db.add(report)
        db.flush()
        context.ids[report_ref] = str(report.id)

    db.commit()
