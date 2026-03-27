"""Given 使用者本月高階教練剩餘額度 — Aggregate Given"""

import uuid

from behave import given


@given('使用者 "{email}" 本月高階教練剩餘額度為 {count:d}')
def step_impl(context, email, count):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    # 將剩餘額度存入 context.memo 供後續驗證
    context.memo[f"coach_quota_{email}"] = count
