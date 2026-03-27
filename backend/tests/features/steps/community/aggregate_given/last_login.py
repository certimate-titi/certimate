"""Given step: 使用者 "{email}" 的最後登入日為 {date_str}"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.user import User


@given('使用者 "{email}" 的最後登入日為 {date_str}')
def step_impl(context, email, date_str):
    db = context.db_session
    user_id = uuid.UUID(context.ids[email])
    user = db.query(User).filter_by(id=user_id).first()
    user.last_login_at = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    db.commit()
