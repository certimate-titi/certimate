"""Then 學習鷹架清單應包含/不應包含 chapter_heading（TASK-02）— ReadModel Then"""

from behave import then


def _headings(context) -> list[str]:
    data = context.last_response.json()
    return [s.get("chapter_heading") for s in data.get("scaffolds", [])]


@then('學習鷹架清單應包含 chapter_heading 為 "{heading}" 的項目')
def step_contains(context, heading):
    headings = _headings(context)
    assert heading in headings, (
        f"鷹架清單應包含 '{heading}'，實際：{headings}"
    )


@then('學習鷹架清單不應包含 chapter_heading 為 "{heading}" 的項目')
def step_not_contains(context, heading):
    headings = _headings(context)
    assert heading not in headings, (
        f"鷹架清單不應包含 '{heading}'，實際：{headings}"
    )
