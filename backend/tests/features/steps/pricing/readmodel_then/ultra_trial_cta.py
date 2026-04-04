"""Then ULTRA 方案應顯示免費試用 CTA — ReadModel Then"""

from behave import then


@then('ULTRA_1599 方案應顯示「免費試用 14 天」CTA')
def step_impl(context):
    response = context.last_response
    data = response.json()

    plans = data.get("plans", [])
    ultra = next((p for p in plans if p.get("plan_name") == "ULTRA_1599"), None)
    assert ultra is not None, "找不到 ULTRA_1599 方案"

    cta = ultra.get("cta_text", "")
    assert cta == "免費試用 14 天", (
        f"ULTRA_1599 CTA 應為 '免費試用 14 天'，但得到 '{cta}'"
    )
