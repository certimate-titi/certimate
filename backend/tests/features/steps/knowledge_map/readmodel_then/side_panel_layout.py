"""Then 畫面的右側（25%）為樹狀的「互動心智圖知識點導航」 — Read Model"""

from behave import then


@then('畫面的右側（25%）為樹狀的「互動心智圖知識點導航」')
def side_panel_layout(context):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "mind_map_nav" in data, (
        f"回應缺少 'mind_map_nav' 欄位，實際欄位: {list(data.keys())}"
    )

    nav = data["mind_map_nav"]
    assert nav.get("width") == "25%", (
        f"預期 mind_map_nav.width == '25%'，實際: {nav.get('width')}"
    )
    assert "knowledge_tree" in nav, (
        f"mind_map_nav 缺少 'knowledge_tree'，實際欄位: {list(nav.keys())}"
    )
