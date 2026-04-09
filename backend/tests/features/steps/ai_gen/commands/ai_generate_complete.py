"""When 後端 AI 生成服務依序完成各階段 — Command"""

from behave import when


@when('後端 AI 生成服務依序完成各階段')
def step_impl(context):
    """模擬後端 AI 生成服務完成所有階段並推送 SSE 進度。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    task_id = context.memo.get("exam_task_id", 100)

    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.memo["sse_progress_events"] = []
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda self: {}, "text": "not found"})()
        return

    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/exam-tasks/{task_id}/progress",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
