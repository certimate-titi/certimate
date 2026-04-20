"""Then — API 回應 body 驗證。"""

from behave import then


@then('回應狀態碼應為 {code:d}')
def step_check_status(context, code):
    assert context.last_response is not None, "尚未發送請求"
    assert context.last_response.status_code == code, (
        f"expected {code}, got {context.last_response.status_code}: "
        f"{context.last_response.text[:300]}"
    )


@then('錯誤訊息包含 "{substr}"')
def step_check_error_message(context, substr):
    body = context.last_response.json()
    # FastAPI HTTPException: {"detail": {"message": "..."}}
    detail = body.get("detail", {})
    msg = detail.get("message", "") if isinstance(detail, dict) else str(detail)
    assert substr in msg, f'"{substr}" 不在錯誤訊息 "{msg}" 中'


@then('回傳 "nodes" 為空陣列')
def step_check_nodes_empty(context):
    body = context.last_response.json()
    assert body.get("nodes") == [], f"nodes 非空: {body.get('nodes')}"


@then('回傳 "empty_reason" 為 "{reason}"')
def step_check_empty_reason(context, reason):
    body = context.last_response.json()
    assert body.get("empty_reason") == reason, (
        f'empty_reason={body.get("empty_reason")} != {reason}'
    )
