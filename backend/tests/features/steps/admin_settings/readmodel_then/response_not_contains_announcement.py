"""Then 回應不應包含標題為 ... 的公告 — Readmodel Then"""

from behave import then


@then('回應不應包含標題為 "{title}" 的公告')
def step_impl(context, title):
    response = context.last_response
    data = response.json()

    # Response could be {"announcements": [...]} or a list
    announcements = data if isinstance(data, list) else data.get("announcements", data.get("items", []))

    titles = [a.get("title") for a in announcements]
    assert title not in titles, \
        f"回應不應包含標題為 '{title}' 的公告，但找到了。所有標題: {titles}"
