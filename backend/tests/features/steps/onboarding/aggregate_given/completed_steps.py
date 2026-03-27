"""Given 使用者已完成 Step 1 至 Step 3 的設定 — Aggregate Given"""

from behave import given


@given('使用者 "{email}" 已完成 Step 1 至 Step 3 的設定：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    context.memo["current_token"] = token
    context.memo["current_email"] = email

    # Store the settings from the table for later verification
    row = context.table[0]
    context.memo["onboarding_display_name"] = row["顯示名稱"]
    context.memo["onboarding_subjects"] = row["備考科目"]
    context.memo["onboarding_daily_minutes"] = row["每日學習時間"]
    context.memo["onboarding_preference"] = row["偏好學習方式"]
