"""Given 系統中有以下方案權限對照表 — Aggregate Given"""

from behave import given

from app.models.plan_quota import PlanQuota


@given('系統中有以下方案權限對照表：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        plan = row["方案"]
        daily_ai = row["AI 對話次數/日"]
        monthly_upload = row["上傳數/月"]
        monthly_exam = row["考試數/月"]
        monthly_vision = row["Vision OCR/月"]

        quota = PlanQuota(
            plan=plan,
            daily_ai_chats=None if daily_ai == "無限" else int(daily_ai),
            monthly_uploads=None if monthly_upload == "無限" else int(monthly_upload),
            monthly_exams=None if monthly_exam == "無限" else int(monthly_exam),
            monthly_vision_pages=None if monthly_vision == "無限" else int(monthly_vision),
        )
        db.add(quota)

    db.commit()
