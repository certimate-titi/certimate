"""Then 回應應包含溯源引用 — ReadModel Then"""

from behave import then


@then('回應應包含溯源引用：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    citation = data.get("source_citation", {})
    for row in context.table:
        field = row["欄位"]
        actual = citation.get(field)
        assert actual is not None and str(actual).strip() != "", \
            f"溯源引用欄位 '{field}' 不應為空，實際 '{actual}'"
