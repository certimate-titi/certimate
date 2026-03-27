"""Given 使用者 "..." 已登入系統 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已登入系統')
def step_impl(context, email):
    context.memo["logged_in_email"] = email
