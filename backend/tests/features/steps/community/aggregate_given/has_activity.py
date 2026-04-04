"""Given step: 使用者 "{email}" 在本週有學習活動"""

from behave import given


@given('使用者 "{email}" 在本週有學習活動')
def step_impl(context, email):
    if "activities" not in context.memo:
        context.memo["activities"] = {}
    context.memo["activities"][email] = {
        "study_hours": 5.0,
        "exams_completed": 2,
        "questions_answered": 80,
    }
