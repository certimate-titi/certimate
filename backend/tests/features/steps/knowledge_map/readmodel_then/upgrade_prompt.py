"""Then 面板周圍彈出極高質感的升級提示 — Read Model (Paywall)"""

from behave import then


@then('面板周圍彈出極高質感的升級提示「{message}」')
def upgrade_prompt(context, message):
    response = context.last_response
    status = response.status_code

    # Accept either 403 or 200 with paywall info
    assert status in (200, 403), (
        f"預期 HTTP 200 或 403，實際 {status}: {response.text}"
    )

    data = response.json()
    # When 403, FastAPI wraps in {"detail": {...}}
    if "detail" in data and isinstance(data["detail"], dict):
        data = data["detail"]

    assert "upgrade_prompt" in data, (
        f"回應缺少 'upgrade_prompt' 欄位，實際欄位: {list(data.keys())}"
    )
    assert message in data["upgrade_prompt"], (
        f"upgrade_prompt 應包含 '{message}'，實際: {data['upgrade_prompt']}"
    )
