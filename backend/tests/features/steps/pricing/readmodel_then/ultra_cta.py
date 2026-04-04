"""Then ULTRA 方案 CTA 為升級或免費試用 — ReadModel Then"""

from behave import then


@then('ULTRA_1599 方案的 CTA 應為「升級」或「免費試用 14 天」')
def step_impl(context):
    response = context.last_response
    data = response.json()

    plans = data.get("plans", [])
    ultra = next((p for p in plans if p.get("plan_name") == "ULTRA_1599"), None)
    assert ultra is not None, "找不到 ULTRA_1599 方案"

    cta = ultra.get("cta_text", "")
    valid_ctas = ["升級", "免費試用 14 天"]
    assert cta in valid_ctas, (
        f"ULTRA_1599 CTA 應為 {valid_ctas} 之一，但得到 '{cta}'"
    )
