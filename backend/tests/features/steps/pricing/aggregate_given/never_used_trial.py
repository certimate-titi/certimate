"""Given 使用者從未使用過 ULTRA 免費試用 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 從未使用過 ULTRA 免費試用')
def step_impl(context, email):
    # No-op: default state, user has never used trial
    pass
