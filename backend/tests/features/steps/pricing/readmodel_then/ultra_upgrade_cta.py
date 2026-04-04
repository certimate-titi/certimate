"""Then ULTRA 方案應顯示升級 CTA — ReadModel Then"""

from behave import then


@then('ULTRA_1599 方案應顯示「升級」CTA（非「免費試用」）')
def step_impl(context):
    response = context.last_response
    data = response.json()

    plans = data.get("plans", [])
    ultra = next((p for p in plans if p.get("plan_name") == "ULTRA_1599"), None)
    assert ultra is not None, "找不到 ULTRA_1599 方案"

    cta = ultra.get("cta_text", "")
    assert cta == "升級", (
        f"ULTRA_1599 CTA 應為 '升級'，但得到 '{cta}'"
    )
    assert "免費試用" not in cta, "CTA 不應包含 '免費試用'"
