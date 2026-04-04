"""Then 回應應包含 N 個可訂閱方案 — ReadModel Then"""

from behave import then


@then('回應應包含 {count:d} 個可訂閱方案（FREE、PRO_199、PRO_PLUS_399、ULTRA_1599）')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    plans = data.get("plans", [])
    assert len(plans) == count, (
        f"應包含 {count} 個方案，但得到 {len(plans)}"
    )

    expected_names = {"FREE", "PRO_199", "PRO_PLUS_399", "ULTRA_1599"}
    actual_names = {p.get("plan_name") for p in plans}
    assert expected_names == actual_names, (
        f"方案名稱不符，期望 {expected_names}，得到 {actual_names}"
    )
