"""Given 使用者進入 Step 2 選擇備考科目 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 進入 Step 2 選擇備考科目')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email
