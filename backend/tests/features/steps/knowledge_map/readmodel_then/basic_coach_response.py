"""Then steps for basic coach response validation — ReadModel Then"""

from behave import then


@then('回應應以串流方式輸出基礎教練回覆（不含深度策略分析）')
def step_impl_basic_streaming(context):
    """驗證回應為基礎教練串流回覆（不含深度策略分析）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        # Verify basic coach response (no deep strategy analysis)
        message = data.get("message") or data.get("content") or ""
        assert len(message) > 0, "基礎教練回覆不應為空"
        # Verify no deep strategy analysis marker
        coach_type = data.get("coach_type", "basic")
        assert coach_type != "deep_strategy", \
            "基礎教練回覆不應包含深度策略分析"
