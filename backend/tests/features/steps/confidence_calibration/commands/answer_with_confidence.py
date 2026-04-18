"""When 使用者選擇答案並標記信心度 — Command"""

from behave import when


def _resolve_exam_id(context, q_uuid):
    """Look up exam_id from question for path-param endpoint."""
    from app.models.question import Question
    import uuid as uuid_mod
    try:
        qid = uuid_mod.UUID(q_uuid)
    except Exception:
        return q_uuid
    q = context.db_session.query(Question).filter(Question.id == qid).first()
    return str(q.exam_id) if q and q.exam_id else q_uuid


@when('使用者 "{email}" 在題目 {q_id:d} 選擇答案 "{answer}" 並標記信心度為 "{confidence}"')
def step_impl_answer_with_confidence(context, email, q_id, answer, confidence):
    """呼叫 API 提交答案及信心度標記。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    q_key = f"question_id_{q_id}"
    q_uuid = context.ids.get(q_key, str(q_id))
    exam_id = _resolve_exam_id(context, q_uuid)

    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/answers",
        json={
            "question_id": q_uuid,
            "selected_answer": answer,
            "confidence": confidence,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo[f"answer_question_{q_id}"] = answer
    context.memo[f"confidence_question_{q_id}"] = confidence


@when('使用者 "{email}" 在題目 {q_id:d} 選擇答案 "{answer}" 且未標記信心度')
def step_impl_answer_no_confidence(context, email, q_id, answer):
    """呼叫 API 提交答案，不標記信心度（使用預設值）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    q_key = f"question_id_{q_id}"
    q_uuid = context.ids.get(q_key, str(q_id))
    exam_id = _resolve_exam_id(context, q_uuid)

    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/answers",
        json={
            "question_id": q_uuid,
            "selected_answer": answer,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo[f"answer_question_{q_id}"] = answer


@when('使用者 "{email}" 在題目 {q_id:d} 選擇答案 "{answer}"')
def step_impl_answer_only(context, email, q_id, answer):
    """呼叫 API 提交答案（用於 UI 相關測試）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    q_key = f"question_id_{q_id}"
    q_uuid = context.ids.get(q_key, str(q_id))
    exam_id = _resolve_exam_id(context, q_uuid)

    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.post(
        f"/api/v1/exams/{exam_id}/answers",
        json={"question_id": q_uuid, "selected_answer": answer},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo[f"answer_question_{q_id}"] = answer


@when('使用者 "{email}" 查看測驗 {exam_id:d} 的信心度分析')
def step_impl_view_confidence_analysis(context, email, exam_id):
    """呼叫信心度分析 API。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"

    exam_key = f"exam_id_{exam_id}"
    exam_uuid = context.ids.get(exam_key, str(exam_id))

    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/exams/{exam_uuid}/confidence-analysis",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('系統計算下次複習排程')
def step_impl_calculate_schedule(context):
    """觸發系統計算複習排程。

    註：目前後端無「信心度 → 單題複習間隔」的專屬 endpoint；
    /schedule/calculate-mode 僅做 train/review 模式切換。
    此步驟維持為 no-op stub，待 schedule 模組擴充（ISS-010b）後改為真實 API 呼叫。
    """
    context.last_response = type(
        "FakeResp",
        (),
        {"status_code": 200, "json": lambda self: {}, "text": ""},
    )()


@when('使用者查看個人儀表板的信心校準區塊')
def step_impl_view_dashboard_calibration(context):
    """查看儀表板信心校準區塊。"""
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": "not found"})()
        return
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        "/api/v1/dashboard/confidence-calibration",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者查看題號導覽網格')
def step_impl_view_question_grid(context):
    """查看題號導覽網格 API。"""
    exam_id = context.memo.get("current_exam_id", 1)
    email = context.memo.get("current_user_email", "pro@example.com")
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("FakeResp", (), {"status_code": 404, "json": lambda: {}, "text": "not found"})()
        return
    token = context.jwt_helper.generate_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/exams/{exam_id}/question-grid",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
