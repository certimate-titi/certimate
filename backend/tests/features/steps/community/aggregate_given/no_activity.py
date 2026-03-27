"""Given step: 使用者 "{email}" 本週無任何學習活動"""

from behave import given


@given('使用者 "{email}" 本週無任何學習活動')
def step_impl(context, email):
    if "activities" not in context.memo:
        context.memo["activities"] = {}
    context.memo["activities"][email] = None
