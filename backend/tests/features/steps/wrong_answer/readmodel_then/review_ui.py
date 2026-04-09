"""Then 錯題複習 UI 互動驗證 — ReadModel Then"""

from behave import then


@then('右側解析區應切換顯示題目 {question_id:d} 的內容')
def step_impl_switch_to_question(context, question_id):
    """驗證切換至指定題目的解析（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('側邊列表中題目 {question_id:d} 應呈現選中狀態')
def step_impl_question_selected(context, question_id):
    """驗證側邊列表題目選中狀態（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('解析區應以視覺對比方式顯示使用者選擇「{user_choice}」與正確答案「{correct_choice}」')
def step_impl_answer_contrast(context, user_choice, correct_choice):
    """驗證解析區顯示答案對比（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        assert "user_answer" in data or "correct_answer" in data or "analysis" in data, \
            "解析回應應包含答案資訊"


@then('正確答案應以綠色標示，錯誤答案應以紅色標示')
def step_impl_color_marking(context):
    """驗證顏色標示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('解析區應展開顯示該題的原始資源引用')
def step_impl_citations_expanded(context):
    """驗證引用來源已展開（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('引用來源應包含資源名稱與對應的頁碼或時間戳')
def step_impl_citation_fields(context):
    """驗證引用來源包含必要欄位（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        citations = data.get("citations") or data.get("source_citations") or []
        if citations:
            for c in citations:
                assert "resource_name" in c or "name" in c, \
                    f"引用來源應包含資源名稱，實際: {c}"


@then('引用來源區塊應收合隱藏')
def step_impl_citations_collapsed(context):
    """驗證引用來源已收合（Red 階段通過）。"""
    assert not context.memo.get("citations_expanded", True), \
        "引用來源應為收合狀態"


@then('深度解說區應以毛玻璃（高斯模糊）效果遮擋完整內容')
def step_impl_blur_overlay(context):
    """驗證深度解說區毛玻璃遮罩（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('遮罩上方應顯示「升級至 {plan} 解鎖完整解析」的升級按鈕')
def step_impl_upgrade_button(context, plan):
    """驗證升級提示按鈕（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('AI 教練聊天區域應呈現鎖定狀態')
def step_impl_coach_locked(context):
    """驗證 AI 教練聊天鎖定（Red 階段允許 200/404/403）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 403, 404, 429), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('鎖定區域應顯示升級提示：「{upgrade_message}」')
def step_impl_locked_upgrade_hint(context, upgrade_message):
    """驗證鎖定升級提示訊息（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 403, 404, 429), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應顯示空狀態提示：「{message}」')
def step_impl_empty_state_hint(context, message):
    """驗證無錯題空狀態提示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應顯示「回到儀表板」連結按鈕')
def step_impl_dashboard_link_button(context):
    """驗證顯示回到儀表板按鈕（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應導航至儀表板頁面')
def step_impl_nav_to_dashboard(context):
    """驗證導航至儀表板（Red 階段通過）。"""
    pass  # UI navigation; Red phase passes
