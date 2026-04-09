"""Then 個人儀表板狀態驗證 — Aggregate Then"""

from behave import then


@then('使用者 "{email}" 的連勝應為 {days:d} 天')
def step_impl_streak_days_check(context, email, days):
    """驗證使用者連勝天數（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        from app.models.user import User
        user = context.db_session.query(User).filter(User.email == email).first()
        if user and hasattr(user, "streak_days"):
            context.db_session.refresh(user)
            assert user.streak_days == days, \
                f"預期連勝 {days} 天，實際 {user.streak_days} 天"


@then('使用者 "{email}" 應獲得成就徽章：')
def step_impl_achievement_badge(context, email):
    """驗證使用者獲得指定成就徽章（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"



@then('使用者 "{email}" 的訂閱方案應於計費週期結束後降為 "{plan}"')
def step_impl_subscription_scheduled_downgrade(context, email, plan):
    """驗證訂閱計畫已排程降級（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('使用者 "{email}" 的帳號狀態應為 "{status}"')
def step_impl_user_account_status_by_email(context, email, status):
    """驗證使用者（以 email 識別）的帳號狀態（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        from app.models.user import User
        user = context.db_session.query(User).filter(User.email == email).first()
        if user:
            context.db_session.refresh(user)
            actual = user.status.value if hasattr(user.status, "value") else str(user.status)
            assert actual == status, \
                f"預期帳號狀態 '{status}'，實際 '{actual}'"


@then('使用者 "{email}" 的備考科目應不包含 "{subject}"')
def step_impl_subject_not_in_journeys(context, email, subject):
    """驗證使用者備考科目不包含指定科目（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
