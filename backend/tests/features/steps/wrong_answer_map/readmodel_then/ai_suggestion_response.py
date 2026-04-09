"""Then steps for AI learning suggestion response validation."""

from behave import then


@then("建議應優先針對紅色節點（mastery_rate 最低者）")
def step_impl_prioritize_red(context):
    """驗證 AI 建議優先針對 mastery_rate 最低的紅色節點。"""
    response = context.last_response
    assert response.status_code == 200, f"期望 200，實際 {response.status_code}"
    data = response.json()

    suggestions = data.get("suggestions") or data.get("data") or []
    assert len(suggestions) > 0, "建議清單不應為空"

    # 確認第一條建議針對掌握度最低的節點（紅色節點優先）
    first_suggestion = suggestions[0]
    assert "current_rate" in first_suggestion, "建議應包含 current_rate"

    # 確認排序：current_rate 應由低到高排列（最弱節點優先）
    rates = [s.get("current_rate", 100) for s in suggestions]
    assert rates == sorted(rates), f"建議應由掌握度最低排到最高，實際順序：{rates}"


# 注意："每條建議應包含：" step 已定義於 b2b/readmodel_then/ai_suggestions.py，
# 此處不重複定義以避免 AmbiguousStep 衝突。
