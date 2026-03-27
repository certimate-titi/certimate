"""Then 異常應標記為已歸類 — Aggregate Then"""

from behave import then

from app.models.anomaly_record import AnomalyRecord


@then('異常 "{error_id}" 應標記為「已歸類」')
def step_impl(context, error_id):
    response = context.last_response
    data = response.json()

    items = data if isinstance(data, list) else data.get("items", data.get("data", []))

    matched = None
    for item in items:
        if item.get("error_id") == error_id:
            matched = item
            break

    assert matched is not None, f"回應中找不到異常 '{error_id}'"
    assert matched.get("classified") is True or matched.get("status") == "classified", \
        f"異常 '{error_id}' 應標記為已歸類，實際: {matched}"
