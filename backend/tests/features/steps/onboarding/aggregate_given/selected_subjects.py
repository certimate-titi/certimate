"""Given 使用者已選擇多個備考科目 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已選擇 "{subject1}" 和 "{subject2}"')
def step_impl(context, email, subject1, subject2):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email
    context.memo["selected_subjects"] = [subject1, subject2]
