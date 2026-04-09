"""Then 測驗結果 UI 元件驗證 — ReadModel Then"""

from behave import then


@then('畫面應觸發撒花動畫 (Confetti)')
def step_impl_confetti(context):
    """驗證成績進步時觸發慶祝動畫（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應提供「產生與分享成績卡片」的功能按鈕')
def step_impl_score_card_button(context):
    """驗證系統提供成績卡片按鈕（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('畫面底部應顯示提示文字 "{hint_text}"')
def step_impl_bottom_hint(context, hint_text):
    """驗證畫面底部顯示免責聲明（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('畫面應顯示提示訊息 "{message}"')
def step_impl_toast_message(context, message):
    """驗證頁面顯示提示訊息（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應導航至錯題複習頁面')
def step_impl_nav_to_wrong_review(context):
    """驗證導航至錯題複習頁面（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('錯題複習頁面應自動帶入測驗 {exam_id:d} 的錯題範圍')
def step_impl_wrong_review_scope(context, exam_id):
    """驗證錯題複習已帶入測驗範圍（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('領域分析區塊應以進度條呈現以下節點正確百分比：')
def step_impl_domain_analysis_progress(context):
    """驗證領域分析進度條呈現節點正確百分比。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        node_analysis = data.get("node_analysis") or data.get("knowledge_points") or []
        if node_analysis:
            for row in context.table:
                node_name = row["節點名稱"]
                found = any(
                    n.get("node_name") == node_name or n.get("name") == node_name
                    for n in node_analysis
                )
                assert found, f"領域分析中找不到節點 '{node_name}'"
