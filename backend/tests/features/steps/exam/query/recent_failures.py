"""Query 最近失敗測驗 — Query (Layer 3)"""

from behave import when, then


@when('使用者 "{email}" 查詢最近失敗的測驗')
def step_query_recent_failures(context, email):
    """呼叫 GET /api/v1/exams/recent-failures（前端 /review Layer 3 用）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/exams/recent-failures",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@then('回應應包含 {count:d} 個失敗測驗')
def step_assert_recent_failures_count(context, count):
    """驗證回應 failures 陣列長度。"""
    data = context.last_response.json()
    failures = data.get("failures", [])
    assert len(failures) == count, \
        f"預期 {count} 個失敗測驗，實際 {len(failures)}"
