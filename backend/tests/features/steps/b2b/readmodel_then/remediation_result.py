"""Then steps — 補救試卷結果回應驗證."""
from behave import then


@then('系統應生成包含 {count:d} 題的補救試卷')
def step_remediation_question_count(context, count):
    """Verify remediation exam has expected number of questions."""

    resp = context.last_response.json()
    assert resp.get("question_count") == count, \
        f"Expected {count} questions, got {resp.get('question_count')}"


@then('試卷中各能力的題數分配應為：')
def step_remediation_distribution(context):
    """Verify question distribution across competencies."""

    resp = context.last_response.json()
    distribution = resp.get("distribution", [])
    for row in context.table:
        label = row["能力節點"]
        expected_count = int(row["題數"])
        found = next((d for d in distribution if d["label"] == label), None)
        assert found is not None, f"Missing distribution for '{label}'"
        assert found["count"] == expected_count, \
            f"Expected {expected_count} for '{label}', got {found['count']}"


@then('各能力應各分配 {count:d} 題')
def step_all_competencies_equal(context, count):
    """Verify all competencies have equal question count."""

    resp = context.last_response.json()
    distribution = resp.get("distribution", [])
    for d in distribution:
        assert d["count"] == count, \
            f"Expected {count} for '{d['label']}', got {d['count']}"
