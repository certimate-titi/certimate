"""When 知識心智圖 UI 互動操作 — Command"""

from behave import when


@when('使用者 "{email}" 在心智圖導覽區的搜尋框輸入 "{keyword}"')
def step_impl_search_knowledge_node(context, email, keyword):
    """呼叫 API 以關鍵字搜尋知識節點。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.get(
        f"/api/v1/knowledge-nodes/search?q={keyword}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["km_token"] = token
    context.memo["km_search_keyword"] = keyword


@when('使用者點擊資源面板的摺疊按鈕')
def step_impl_collapse_resource_panel(context):
    """呼叫 API 折疊資源面板（UI step）。"""
    token = context.memo.get("km_token")
    if token:
        response = context.api_client.get(
            "/api/v1/knowledge-map/resource-panel/collapse",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('使用者再次點擊展開按鈕')
def step_impl_expand_resource_panel(context):
    """呼叫 API 展開資源面板（UI step）。"""
    token = context.memo.get("km_token")
    if token:
        response = context.api_client.get(
            "/api/v1/knowledge-map/resource-panel/expand",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('使用者點擊刪除按鈕')
def step_impl_click_delete_button(context):
    """呼叫 API 觸發刪除確認 Modal（UI step）。"""
    token = context.memo.get("km_token")
    resource_id = context.memo.get("selected_resource_id", "1")
    if token:
        response = context.api_client.get(
            f"/api/v1/resources/{resource_id}/delete-confirm",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('使用者在 Modal 中點擊「取消」')
def step_impl_click_modal_cancel(context):
    """取消刪除 Modal（UI step）。"""
    token = context.memo.get("km_token")
    if token:
        response = context.api_client.get(
            "/api/v1/knowledge-map/modal/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('使用者 "{email}" 確認刪除該文件')
def step_impl_confirm_delete_document(context, email):
    """確認刪除資源（呼叫 DELETE API）— 對齊前端 DELETE /resources/{id}。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.memo.get("km_token") or context.jwt_helper.create_token(str(user.id))
    resource_id = context.memo.get("selected_resource_id")
    assert resource_id, "尚未選中資源（需先執行 Given 在資源面板選中一份文件）"
    response = context.api_client.delete(
        f"/api/v1/resources/{resource_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者在 Modal 中點擊「確認刪除」')
def step_impl_click_modal_confirm_delete(context):
    """確認刪除資源（呼叫 DELETE API）。"""
    token = context.memo.get("km_token")
    resource_id = context.memo.get("selected_resource_id", "1")
    if token:
        response = context.api_client.delete(
            f"/api/v1/resources/{resource_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('左側面板載入 YouTube 嵌入播放器')
def step_impl_load_youtube_player(context):
    """呼叫 API 載入 YouTube 嵌入播放器（含時間戳）。"""
    token = context.memo.get("km_token")
    timestamp = context.memo.get("video_timestamp", "00:00:00")
    if token:
        response = context.api_client.get(
            f"/api/v1/knowledge-map/youtube-player?timestamp={timestamp}",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('使用者點擊快速提問 Chip「用簡單的話解釋這個概念」')
def step_impl_click_quick_question_chip(context):
    """點擊快速提問 Chip，填入輸入框（UI step）。"""
    chip_text = "用簡單的話解釋這個概念"
    context.memo["quick_question_text"] = chip_text
    token = context.memo.get("km_token")
    if token:
        response = context.api_client.get(
            "/api/v1/knowledge-map/quick-question-chips",
            headers={"Authorization": f"Bearer {token}"},
        )
        context.last_response = response
    else:
        context.last_response = type("R", (), {"status_code": 404, "json": lambda s: {}})()


@when('使用者 "{email}" 在 AI 教練對話框輸入「{question}」並按下傳送')
def step_impl_send_ai_coach_message(context, email, question):
    """呼叫 API 傳送 AI 教練訊息。"""
    from app.models.user import User
    user = context.db_session.query(User).filter(User.email == email).first()
    assert user, f"找不到使用者 {email}"
    token = context.jwt_helper.create_token(str(user.id))
    response = context.api_client.post(
        "/api/v1/knowledge-map/ai-coach/chat",
        json={"message": question},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
    context.memo["km_token"] = token
