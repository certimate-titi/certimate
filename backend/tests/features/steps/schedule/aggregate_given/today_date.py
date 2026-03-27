"""Given 今日為某日期 — Aggregate Given"""

from datetime import date

from behave import given


@given('今日為 {date_str}')
def step_impl(context, date_str):
    context.memo["today"] = date.fromisoformat(date_str)
