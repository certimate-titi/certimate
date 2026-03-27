"""Given 使用者個人資料設定 — Aggregate Given"""

import uuid

from behave import given

from app.models.user import User


@given('使用者 "{email}" 的個人資料為：')
def step_impl(context, email):
    db = context.db_session

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    assert user is not None, f"DB 中找不到使用者 '{email}'"

    for row in context.table:
        field = row["欄位"]
        value = row["值"]

        if field == "年齡":
            user.age = int(value)
        elif field == "最高學歷":
            user.education = value
        elif field == "職業":
            user.career = value

    db.commit()
    context.memo["current_user_email"] = email


@given('使用者 "{email}" 的年齡與學歷欄位皆為空')
def step_no_profile(context, email):
    db = context.db_session

    if email not in context.ids:
        raise KeyError(f"找不到使用者 '{email}' 的 ID")
    user_id = uuid.UUID(context.ids[email])

    user = db.query(User).filter_by(id=user_id).first()
    assert user is not None

    user.age = None
    user.education = None
    user.career = None
    db.commit()
    context.memo["current_user_email"] = email
