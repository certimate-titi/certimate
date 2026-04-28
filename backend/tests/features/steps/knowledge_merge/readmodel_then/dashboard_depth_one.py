"""Then 儀表板回應應包含 depth=1 節點清單 — Readmodel Then.

Feature 29 §「儀表板查詢回傳 depth=1 節點清單供雷達圖渲染」.

後端契約：dashboard query API 應回傳該科目所有 depth=1 節點清單與名稱（≤ 6 個）。
目前 GET /api/v1/dashboard 在 `domainStrengths` 欄位以 `domain` (=name) +
`node_id` 提供，因此此 Then 接受任一 (id-like, name-like) 欄位組合。
"""

from behave import then


# Possible (id_field, name_field) tuples that satisfy the contract
_ID_NAME_FIELDS = [
    ("id", "name"),
    ("node_id", "name"),
    ("node_id", "domain"),
    ("id", "domain"),
]


def _extract_depth1_list(response_json):
    """從 dashboard 回應中找出 depth=1 節點清單。

    當前 `GET /api/v1/dashboard` 將 root 節點放在 `domainStrengths`
    （或 `radar.domains`）。回傳該清單，找不到則回傳 None。
    """
    if not isinstance(response_json, dict):
        return None
    for key in ("depth1_nodes", "core_topics", "domainStrengths"):
        val = response_json.get(key)
        if isinstance(val, list):
            return val
    radar = response_json.get("radar")
    if isinstance(radar, dict):
        for key in ("domains", "axes", "nodes"):
            val = radar.get(key)
            if isinstance(val, list):
                return val
    return None


@then('回應應包含 depth=1 節點清單，數量等於 N')
def step_response_contains_depth1_list(context):
    response = context.last_response
    assert response.status_code == 200, (
        f"dashboard 查詢失敗 status={response.status_code}, body={response.text}"
    )
    body = response.json()
    nodes = _extract_depth1_list(body)
    assert nodes is not None, (
        f"回應未包含 depth=1 節點清單欄位（檢查 depth1_nodes / "
        f"core_topics / domainStrengths）。實際 keys={list(body.keys())}"
    )
    expected_n = context.memo.get("expected_depth1_count")
    assert expected_n is not None, "memo 缺 expected_depth1_count（Given 應已寫入）"
    assert len(nodes) == expected_n, (
        f"depth=1 節點數量 {len(nodes)} 不等於 N={expected_n}"
    )
    context.memo["dashboard_depth1_nodes"] = nodes


@then('每個節點應包含 id 與 name 欄位')
def step_each_node_has_id_and_name(context):
    nodes = context.memo.get("dashboard_depth1_nodes")
    assert nodes is not None, (
        "memo 缺 dashboard_depth1_nodes（請先驗證「回應應包含 depth=1 節點清單」）"
    )

    for i, node in enumerate(nodes):
        assert isinstance(node, dict), f"第 {i} 個節點非 dict：{node!r}"
        # 接受任一可識別 id + 名稱組合
        ok = False
        for id_field, name_field in _ID_NAME_FIELDS:
            if node.get(id_field) and node.get(name_field):
                ok = True
                break
        assert ok, (
            f"第 {i} 個節點缺少 id 或 name 欄位（接受 "
            f"{_ID_NAME_FIELDS}）。實際 keys={list(node.keys())}"
        )
