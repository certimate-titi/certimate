"""Then API 回應公告數量與標題驗證 — ReadModel Then (feature 24)"""

from behave import then


def _extract_announcements(data):
    """從 API 回應中萃取公告列表。"""
    if isinstance(data, list):
        return data
    return data.get("announcements", data.get("items", []))


@then('API 回應應包含 {count:d} 則公告')
def step_response_contains_n_announcements(context, count):
    """驗證 API 回應包含指定數量的公告。"""
    response = context.last_response
    data = response.json()
    announcements = _extract_announcements(data)
    assert len(announcements) == count, \
        f"API 回應應包含 {count} 則公告，實際包含 {len(announcements)} 則。資料: {data}"


@then('公告標題應為 "{title}"')
def step_response_announcement_title(context, title):
    """驗證 API 回應中的公告標題。"""
    response = context.last_response
    data = response.json()
    announcements = _extract_announcements(data)
    titles = [a.get("title") for a in announcements]
    assert title in titles, \
        f"公告標題應包含 '{title}'，實際標題列表: {titles}"
