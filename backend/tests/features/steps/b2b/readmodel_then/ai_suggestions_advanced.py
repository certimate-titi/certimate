"""Then steps — AI 補強建議進階驗證."""
from behave import then


@then('回應應包含至少 {min_count:d} 條建議')
def step_min_suggestion_count(context, min_count):
    """Verify minimum number of suggestions."""

    resp = context.last_response.json()
    suggestions = resp.get("suggestions", [])
    assert len(suggestions) >= min_count, \
        f"Expected at least {min_count} suggestions, got {len(suggestions)}"


@then('建議應優先針對分數最低的能力（{topics}）')
def step_suggestions_prioritize_weakest(context, topics):
    """Verify suggestions prioritize the weakest competencies."""

    resp = context.last_response.json()
    suggestions = resp.get("suggestions", [])
    expected_topics = [t.strip() for t in topics.split("\u3001")]
    suggestion_topics = [s["topic"] for s in suggestions[:len(expected_topics)]]
    for topic in expected_topics:
        assert topic in suggestion_topics, \
            f"Expected topic '{topic}' in top suggestions, got {suggestion_topics}"


@then('回應應包含一條 action_type 為 "{action_type}" 的整體建議')
def step_suggestion_has_action_type(context, action_type):
    """Verify a suggestion with specific action_type exists."""

    resp = context.last_response.json()
    suggestions = resp.get("suggestions", [])
    found = any(s.get("action_type") == action_type for s in suggestions)
    assert found, f"No suggestion with action_type='{action_type}' found"
