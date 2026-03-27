"""Then 畫面的主戰場（左側 75%）預設載入「空白的 AI 教練對話與動態溯源內容區」 — Read Model"""

from behave import then


@then('畫面的主戰場（左側 75%）預設載入「空白的 AI 教練對話與動態溯源內容區」')
def main_panel_layout(context):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "coach_panel" in data, (
        f"回應缺少 'coach_panel' 欄位，實際欄位: {list(data.keys())}"
    )

    panel = data["coach_panel"]
    assert panel.get("width") == "75%", (
        f"預期 coach_panel.width == '75%'，實際: {panel.get('width')}"
    )
