"""Given 系統中有以下方案定義 — Aggregate Given"""

from behave import given

from app.models.plan_quota import PlanQuota


@given('系統中有以下方案定義：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        plan_name = row["方案"]
        monthly_fee = int(row["月費"])

        def _parse_int_or_none(val):
            if val in ("無限", "null", ""):
                return None
            return int(val)

        daily_ai = _parse_int_or_none(row["AI 對話/日"])
        uploads = _parse_int_or_none(row["上傳/月"])
        exams = _parse_int_or_none(row["考試/月"])
        vision = _parse_int_or_none(row["Vision OCR/月"])

        existing = db.query(PlanQuota).filter_by(plan=plan_name).first()
        if existing:
            existing.daily_ai_chats = daily_ai
            existing.monthly_uploads = uploads
            existing.monthly_exams = exams
            existing.monthly_vision_pages = vision
        else:
            quota = PlanQuota(
                plan=plan_name,
                daily_ai_chats=daily_ai,
                monthly_uploads=uploads,
                monthly_exams=exams,
                monthly_vision_pages=vision,
                max_file_size_mb=100,
            )
            db.add(quota)

    db.commit()
