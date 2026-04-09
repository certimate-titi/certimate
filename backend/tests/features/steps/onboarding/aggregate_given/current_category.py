"""Given 目前選擇的分類 — Aggregate Given"""

from behave import given


@given('目前選擇的分類為 "{category}"')
def step_impl(context, category):
    """記錄目前選擇的分類至 memo。"""
    context.memo["current_category"] = category
