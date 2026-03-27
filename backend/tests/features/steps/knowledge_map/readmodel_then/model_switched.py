"""Then 系統後端引擎無縫切換為 "{model_name}" — Read Model"""

from behave import then

# Feature file may use display names, service returns API identifiers
_MODEL_ALIASES = {
    "Claude 3.5 Sonnet 模型": "claude-3.5-sonnet",
}


@then('系統後端引擎無縫切換為 "{model_name}"')
def model_switched(context, model_name):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "model_used" in data, (
        f"回應缺少 'model_used' 欄位，實際欄位: {list(data.keys())}"
    )

    expected = _MODEL_ALIASES.get(model_name, model_name)
    assert data["model_used"] == expected, (
        f"預期 model_used == '{expected}'，實際: '{data['model_used']}'"
    )
