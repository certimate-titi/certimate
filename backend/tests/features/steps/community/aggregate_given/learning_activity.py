"""Given step: 使用者 "{email}" 在本週有以下學習紀錄："""

from behave import given


@given('使用者 "{email}" 在本週有以下學習紀錄：')
def step_impl(context, email):
    row = context.table[0]
    activity = {
        "study_hours": float(row["學習時數"]),
        "exams_completed": int(row["完成考試數"]),
        "questions_answered": int(row["答題數"]),
    }
    if "activities" not in context.memo:
        context.memo["activities"] = {}
    context.memo["activities"][email] = activity
