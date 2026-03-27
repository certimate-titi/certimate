"""Given 系統中有以下方案限額設定 — Aggregate Given"""

from behave import given

from app.models.plan_quota import PlanQuota


@given('系統中有以下方案限額設定：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        quota = PlanQuota(
            plan=row["方案"],
            monthly_uploads=int(row["每月上傳數"]),
            monthly_exams=int(row["每月考試數"]),
            daily_ai_chats=int(row["每日 AI 對話數"]),
            monthly_vision_pages=int(row["每月 Vision 頁數"]),
        )
        db.add(quota)

    db.commit()
