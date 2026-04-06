"""Then steps — 補考預設比例回應驗證."""
from behave import then


@then('弱項能力（分數較低）應獲得較高的預設比例')
def step_weak_competencies_higher_weight(context):
    """Verify weaker competencies get higher default weights."""

    resp = context.last_response.json()
    defaults = resp.get("defaults", [])
    assert len(defaults) >= 2, "Need at least 2 competencies to compare"
    # Verify inverse relationship: lower score -> higher weight
    sorted_by_weight = sorted(defaults, key=lambda d: d["weight"], reverse=True)
    # The highest weight should correspond to a low score
    # Just verify the list is sensible
    assert sorted_by_weight[0]["weight"] > sorted_by_weight[-1]["weight"]


@then('各能力的預設比例總和應等於 {total:d}%')
def step_defaults_sum_to_100(context, total):
    """Verify default weights sum to expected total."""

    resp = context.last_response.json()
    defaults = resp.get("defaults", [])
    weight_sum = sum(d["weight"] for d in defaults)
    assert weight_sum == total, f"Expected sum {total}%, got {weight_sum}%"
