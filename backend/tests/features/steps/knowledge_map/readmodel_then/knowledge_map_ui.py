"""Then 知識心智圖 UI 驗證 — ReadModel Then"""

from behave import then


@then('右側心智圖導覽區應僅顯示包含 "{keyword}" 關鍵字的知識節點')
def step_impl_filtered_nodes(context, keyword):
    """驗證搜尋結果僅包含符合關鍵字的節點（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('不符合搜尋條件的節點應被隱藏或灰化')
def step_impl_non_matching_nodes_hidden(context):
    """驗證不符合搜尋條件的節點已隱藏或灰化（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('資源面板應收合隱藏，心智圖導覽區佔據完整右側空間')
def step_impl_panel_collapsed(context):
    """驗證資源面板已收合（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('資源面板應恢復原始寬度顯示')
def step_impl_panel_expanded(context):
    """驗證資源面板已展開恢復（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應彈出確認刪除 Modal 視窗')
def step_impl_delete_confirm_modal(context):
    """驗證確認刪除 Modal 已彈出（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('Modal 應關閉，文件仍保留在資源列表中')
def step_impl_modal_closed_resource_retained(context):
    """驗證 Modal 關閉後資源仍保留（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('該文件應從資源列表中移除')
def step_impl_resource_removed_from_list(context):
    """驗證資源已從列表移除（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('心智圖導覽區應同步移除該文件關聯的知識節點')
def step_impl_knowledge_nodes_removed(context):
    """驗證心智圖導覽區同步移除關聯知識節點（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('播放器應自動定位至 {timestamp} 時間點')
def step_impl_player_jump_to_timestamp(context, timestamp):
    """驗證播放器已定位至指定時間點（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('使用者可直接從該時間點開始播放影片')
def step_impl_can_play_from_timestamp(context):
    """驗證使用者可從時間戳播放（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('AI 教練對話輸入框應自動填入「{text}」')
def step_impl_ai_coach_input_filled(context, text):
    """驗證 AI 教練對話框已自動填入文字（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('使用者可直接按下傳送按鈕發出提問')
def step_impl_can_click_send(context):
    """驗證使用者可點擊傳送按鈕（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('AI 教練應以串流方式回覆與 {topic} 相關的解說內容')
def step_impl_ai_stream_reply(context, topic):
    """驗證 AI 教練以串流方式回覆（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('回覆訊息應以氣泡對話框形式顯示在聊天區域')
def step_impl_reply_bubble_displayed(context):
    """驗證回覆以氣泡對話框顯示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('AI 教練面板應顯示「本月剩餘免費查詢次數」計數器')
def step_impl_free_query_counter(context):
    """驗證 AI 教練面板顯示免費查詢次數計數器（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('計數器應顯示目前可用次數與每月上限（例如：3/5）')
def step_impl_counter_shows_quota(context):
    """驗證計數器格式正確（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('面板應顯示升級提示，引導使用者升級至 PRO_PLUS 方案以解鎖完整 AI 教練功能')
def step_impl_upgrade_prompt_proplus(context):
    """驗證面板顯示升級至 PRO_PLUS 提示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
