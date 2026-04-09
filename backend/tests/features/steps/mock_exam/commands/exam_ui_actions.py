"""When 模擬機考 UI 互動操作 — Command"""

import uuid

from behave import when


@when('系統載入測驗的初始畫面')
def step_impl_load_initial_screen(context):
    """呼叫 API 載入測驗初始畫面（AI 打氣訊息）。"""
    exam_id_str = context.memo.get("current_exam_id")
    email = context.memo.get("current_user_email")
    if not exam_id_str or not email:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()
        return
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if not user:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()
        return
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/exams/{exam_id_str}/intro",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('系統時間推進使剩餘時間變為 {minutes:d} 分 {seconds:d} 秒')
def step_impl_advance_time(context, minutes, seconds):
    """模擬系統時間推進（UI step，暫存 memo）。"""
    context.memo["remaining_minutes"] = minutes
    context.memo["remaining_seconds"] = seconds
    # Simulate GET to trigger 404 in Red phase
    exam_id_str = context.memo.get("current_exam_id", "0")
    email = context.memo.get("current_user_email")
    if email:
        from app.models.user import User
        user = context.db_session.query(User).filter(User.email == email).first()
        if user:
            token = context.jwt_helper.create_token(str(user.id))
            response = context.api_client.get(
                f"/api/v1/exams/{exam_id_str}/timer",
                headers={"Authorization": f"Bearer {token}"},
            )
            context.last_response = response


@when('使用者 "{email}" 嘗試關閉測驗頁面')
def step_impl_try_close_exam(context, email):
    """呼叫 API 觸發離開測驗警告（beforeunload）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    exam_id_str = context.memo.get("current_exam_id", "1")
    response = context.api_client.get(
        f"/api/v1/exams/{exam_id_str}/leave-warning",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 瀏覽題目 {question_id:d}')
def step_impl_browse_question(context, email, question_id):
    """呼叫 API 查看指定題目。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    question_uuid = uuid.UUID(int=question_id)
    response = context.api_client.get(
        f"/api/v1/questions/{question_uuid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_question_id"] = str(question_uuid)


@when('使用者 "{email}" 瀏覽題目 {question_id:d} 但未輸入任何內容')
def step_impl_browse_question_no_input(context, email, question_id):
    """呼叫 API 查看題目（未作答，題號網格狀態驗證）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    question_uuid = uuid.UUID(int=question_id)
    response = context.api_client.get(
        f"/api/v1/questions/{question_uuid}/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_question_id"] = str(question_uuid)


@when('使用者 "{email}" 暫停測驗 {exam_id:d}')
def step_impl_pause_exam(context, email, exam_id):
    """呼叫 API 暫停測驗。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    exam_uuid = uuid.UUID(int=exam_id)
    response = context.api_client.post(
        f"/api/v1/exams/{exam_uuid}/pause",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["current_exam_id"] = str(exam_uuid)


@when('經過 {seconds:d} 秒後使用者 "{email}" 恢復測驗 {exam_id:d}')
def step_impl_resume_after_pause(context, seconds, email, exam_id):
    """呼叫 API 恢復測驗（含已暫停秒數）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    exam_uuid = uuid.UUID(int=exam_id)
    response = context.api_client.post(
        f"/api/v1/exams/{exam_uuid}/resume",
        json={"elapsed_pause_seconds": seconds},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 開啟題目總覽格 Modal')
def step_impl_open_overview_modal(context, email):
    """呼叫 API 取得題目總覽格資料。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    exam_id_str = context.memo.get("current_exam_id", "1")
    response = context.api_client.get(
        f"/api/v1/exams/{exam_id_str}/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 在題目導航格中點擊題號 {n:d}')
def step_impl_click_question_nav(context, email, n):
    """呼叫 API 跳轉至指定題號。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    exam_id_str = context.memo.get("current_exam_id", "1")
    response = context.api_client.get(
        f"/api/v1/exams/{exam_id_str}/questions/by-number/{n}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["nav_target_number"] = n


@when('使用者 "{email}" 目前瀏覽題目 {question_id:d}')
def step_impl_currently_viewing_question(context, email, question_id):
    """記錄目前瀏覽的題目（UI 前置狀態）。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    if user:
        token = context.jwt_helper.create_token(str(user.id))
        question_uuid = uuid.UUID(int=question_id)
        response = context.api_client.get(
            f"/api/v1/questions/{question_uuid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
        context.memo["current_question_id"] = str(question_uuid)
