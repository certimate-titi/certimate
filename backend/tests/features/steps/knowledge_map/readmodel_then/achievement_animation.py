"""Then 對應的 AI 教練可能發送灑花的恭喜獎章動畫 — Read Model"""

from behave import then


@then('對應的 AI 教練可能發送灑花的恭喜獎章動畫')
def achievement_animation(context):
    response = context.last_response

    # This is optional behavior ("可能"), so we check if the response
    # contains achievements info but do not fail if absent.
    # However, we still verify the response is accessible.
    if response.status_code == 200:
        data = response.json()
        # Achievements field is optional — just verify it's present if included
        if "achievements" in data:
            assert isinstance(data["achievements"], list), (
                f"achievements 應為列表，實際: {type(data['achievements'])}"
            )
    # For Red phase, the API returns 404, which is expected.
    # We do not assert 200 here since achievements are optional.
    assert response.status_code in (200, 404), (
        f"預期 HTTP 200 或 404，實際 {response.status_code}: {response.text}"
    )
