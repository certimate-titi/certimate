"""Given step: 使用者 "{email}" 有 {n} 份歷史週報"""

import uuid
from datetime import date, timedelta

from behave import given

from app.models.weekly_report import WeeklyReport


@given('使用者 "{email}" 有 {n:d} 份歷史週報')
def step_impl(context, email, n):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    today = date.today()

    for i in range(n):
        week = today - timedelta(weeks=i + 1)
        report = WeeklyReport(
            user_id=user_id,
            report_week=week,
            study_hours=5.0 + i,
            exams_completed=2 + i,
            questions_answered=80 + i * 10,
            progress_summary=f"第 {i + 1} 週的學習表現穩定，繼續保持！",
        )
        db.add(report)
    db.commit()
