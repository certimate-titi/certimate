"""Then 品質閘門結果驗證 — Aggregate Then"""

from behave import then


@then('該題目 quality_flag 應升級為 "{flag}"')
def step_impl(context, flag):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("quality_flag") == flag, \
        f"quality_flag 預期 '{flag}'，實際 '{data.get('quality_flag')}'"


@then('該題目應被丟棄，不入庫')
def step_discarded(context):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    assert data.get("discarded") is True, \
        f"預期題目被丟棄，實際 {data}"
    context.memo["discard_result"] = data


@then('丟棄原因應為 "{reason}"')
def step_discard_reason(context, reason):
    response = context.last_response
    assert response is not None, "沒有 HTTP response"
    data = response.json()
    actual_reason = data.get("discard_reason", "")
    assert reason in actual_reason, \
        f"丟棄原因預期包含 '{reason}'，實際 '{actual_reason}'"
