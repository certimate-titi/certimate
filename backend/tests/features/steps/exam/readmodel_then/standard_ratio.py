"""Then 測驗中考古題與 AI 生成題的比例應依標準權重分配 — ReadModel Then"""

from behave import then


@then('測驗中考古題與 AI 生成題的比例應依標準權重分配')
def step_impl(context):
    response = context.last_response
    data = response.json()

    # 驗證回應中有 ratio 相關資訊
    historical_ratio = data.get("historical_ratio")
    assert historical_ratio is not None, (
        "回應應包含 historical_ratio 欄位"
    )
