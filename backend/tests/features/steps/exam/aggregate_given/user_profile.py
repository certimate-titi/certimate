"""Given 使用者的個人資料為 — Aggregate Given"""

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
    if not user:
        raise ValueError(f"找不到使用者 '{email}'")

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

    # Store for later verification
    context.memo["current_user_email"] = email
    context.memo["user_profile"] = {
        "age": user.age,
        "education": user.education,
        "career": user.career,
    }
