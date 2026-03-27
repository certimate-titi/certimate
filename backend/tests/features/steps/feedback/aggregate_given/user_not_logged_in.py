"""Given 使用者尚未登入 — Aggregate Given"""

from behave import given


@given('使用者尚未登入')
def step_impl(context):
    context.memo["not_logged_in"] = True
