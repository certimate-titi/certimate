"""Given 使用者的個人資料中年齡與學歷皆為空 — Aggregate Given (wrong_answer context)"""

import uuid

from behave import given

from app.models.user import User


@given('使用者 "{email}" 的個人資料中年齡與學歷皆為空')
def step_impl(context, email):
    db = context.db_session

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise ValueError(f"找不到使用者 '{email}'")

    user.age = None
    user.education = None
    user.career = None
    db.commit()

    context.memo["current_user_email"] = email
    context.memo["user_profile"] = None
