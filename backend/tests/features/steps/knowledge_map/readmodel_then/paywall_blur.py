"""Then 該對話框應立即呈現毛玻璃效果被鎖住 — Read Model (Paywall)"""

from behave import then


@then('該對話框應立即呈現毛玻璃效果被鎖住')
def paywall_blur(context):
    response = context.last_response
    status = response.status_code

    # Paywall can be expressed as HTTP 403 or a JSON field
    if status == 403:
        return

    assert status == 200, (
        f"預期 HTTP 403 或 200 (含 paywall 欄位)，實際 {status}: {response.text}"
    )

    data = response.json()
    assert data.get("paywall") is True, (
        f"回應應包含 'paywall': true，實際: {data}"
    )
