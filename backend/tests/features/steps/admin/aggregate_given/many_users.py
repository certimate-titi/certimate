"""Given 系統中有超過 N 筆使用者資料 — Aggregate Given"""

import uuid

from behave import given


@given('系統中有超過 {count:d} 筆使用者資料')
def step_impl_many_users(context, count):
    """建立足夠多筆測試使用者，確保超過 count 筆。"""
    from app.models.user import User

    existing = context.db_session.query(User).count()
    needed = count + 1 - existing
    for i in range(max(0, needed)):
        user = User(
            email=f"paginationuser_{uuid.uuid4().hex[:8]}@example.com",
            display_name=f"Pagination User {i}",
            password_hash="placeholder",
        )
        context.db_session.add(user)
    if needed > 0:
        context.db_session.commit()
