"""Given 使用者未上傳任何資源 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 未上傳任何資源')
def step_impl(context, email):
    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")

    # 不需要做任何操作 — 只是聲明此使用者沒有上傳個人資源
    context.memo[f"no_resources_{email}"] = True
