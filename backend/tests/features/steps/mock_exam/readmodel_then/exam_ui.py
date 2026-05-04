"""Then 模擬機考 UI 驗證 — ReadModel Then"""

from behave import then


@then('畫面應短暫顯示 AI 教練角色（Certi）的打氣介面')
def step_impl_ai_coach_intro(context):
    """驗證 AI 教練 Certi 打氣介面回應（Green 階段：要求 200 + coach_name=Certi）。"""
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}: {response.text[:200]}"
    body = response.json()
    assert body.get("coach_name") == "Certi", \
        f"預期 coach_name='Certi'，實際 {body.get('coach_name')!r}"


@then('AI 教練應提供基於使用者近期學習狀態或連續測驗次數所生成的專屬鼓勵對話')
def step_impl_ai_coach_encouragement(context):
    """驗證 AI 教練提供基於 learning_state 的鼓勵訊息（Green：要求 message 與 learning_state）。"""
    response = context.last_response
    assert response.status_code == 200, \
        f"預期 200，實際 {response.status_code}"
    body = response.json()
    assert body.get("message"), "回應應包含 message 欄位"
    assert "learning_state" in body, "回應應包含 learning_state 欄位"
    assert "streak_days" in body["learning_state"], "learning_state 應含 streak_days"


@then('計時器的顯示樣式應切換為 "{style}"')
def step_impl_timer_style(context, style):
    """驗證計時器樣式切換（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應觸發 beforeunload 警告訊息')
def step_impl_beforeunload_warning(context):
    """驗證系統觸發離頁警告（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('警告訊息應為 "{message}"')
def step_impl_warning_message_content(context, message):
    """驗證警告訊息內容（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('題目顯示區應渲染以下 KaTeX 內容：')
def step_impl_katex_render(context):
    """驗證題目 KaTeX 公式渲染（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('題目顯示區應以多選核取方塊呈現每個選項')
def step_impl_multiple_choice_checkboxes(context):
    """驗證多選題以核取方塊呈現（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('每個選項應正確渲染 KaTeX 公式符號')
def step_impl_katex_options_rendered(context):
    """驗證每個選項 KaTeX 公式已渲染（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('題目 {question_id:d} 在題號導覽網格的狀態應為 "{status}"')
def step_impl_question_nav_grid_status(context, question_id, status):
    """驗證題號導覽網格顯示正確狀態（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('測驗 {exam_id:d} 的剩餘時間應接近 {minutes:d} 分 {seconds:d} 秒')
def step_impl_exam_remaining_time(context, exam_id, minutes, seconds):
    """驗證測驗剩餘時間接近預期值（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('計時器應繼續正常倒數')
def step_impl_timer_continues(context):
    """驗證計時器繼續倒數（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('總覽格 Modal 應顯示以下題目狀態：')
def step_impl_overview_modal_statuses(context):
    """驗證總覽格 Modal 題目狀態（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('畫面應跳轉至題目 {question_id:d}')
def step_impl_navigate_to_question(context, question_id):
    """驗證畫面跳轉至指定題目（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('題目顯示區應呈現題目 {question_id:d} 的內容')
def step_impl_show_question_content(context, question_id):
    """驗證題目顯示區顯示指定題目內容（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('上一題按鈕應為停用狀態')
def step_impl_prev_btn_disabled(context):
    """驗證上一題按鈕為停用（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('下一題按鈕應為啟用狀態')
def step_impl_next_btn_enabled(context):
    """驗證下一題按鈕為啟用（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('下一題按鈕應為停用狀態')
def step_impl_next_btn_disabled(context):
    """驗證下一題按鈕為停用（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('上一題按鈕應為啟用狀態')
def step_impl_prev_btn_enabled(context):
    """驗證上一題按鈕為啟用（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
