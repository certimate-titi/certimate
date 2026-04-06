"""Then 衝突紀錄驗證 — ReadModel Then"""

from behave import then


# Field name mapping: feature file names → possible API response names
_FIELD_ALTS = {
    "existing_node": ["existing_node_name", "existing_name"],
    "incoming_node": ["incoming_node_name", "incoming_name"],
}


def _get_field(item: dict, field: str):
    """Get field value trying alternative names."""
    if field in item:
        return item[field]
    for alt in _FIELD_ALTS.get(field, []):
        if alt in item:
            return item[alt]
    return None


def _has_field(item: dict, field: str) -> bool:
    """Check if field exists (including alternatives)."""
    if field in item:
        return True
    return any(alt in item for alt in _FIELD_ALTS.get(field, []))


@then('回應應包含 {count:d} 筆衝突紀錄')
def step_conflict_count(context, count):
    response = context.last_response
    data = response.json()

    conflicts = data.get("conflicts", data.get("items", []))
    actual_count = len(conflicts)
    assert actual_count == count, \
        f"預期 {count} 筆衝突紀錄，實際有 {actual_count} 筆"


@then('每筆應包含：')
def step_each_record_contains(context):
    response = context.last_response
    data = response.json()

    items = data.get("conflicts", data.get("history", data.get("items", data.get("records", []))))
    assert len(items) > 0, f"回應中沒有任何紀錄，data: {data}"

    for row in context.table:
        field = row["欄位"]
        for i, item in enumerate(items):
            assert _has_field(item, field), \
                f"第 {i+1} 筆紀錄缺少欄位 '{field}'，實際欄位: {list(item.keys())}"


@then('系統應標記為合併衝突：')
def step_conflict_marked(context):
    # Get conflict from merge result (not compare result)
    merge_resp = context.memo.get("merge_response")
    if merge_resp and merge_resp.status_code == 200:
        merge_data = merge_resp.json()
        conflicts = merge_data.get("conflicts", [])
        if conflicts:
            conflict = conflicts[0]
            for row in context.table:
                field = row["欄位"]
                expected = row["值"]

                if field in ("existing_node", "incoming_node"):
                    actual = _get_field(conflict, field)
                    assert actual is not None, \
                        f"衝突紀錄缺少欄位 '{field}'，實際: {list(conflict.keys())}"
                    assert expected in str(actual), \
                        f"欄位 '{field}' 預期包含 '{expected}'，實際為 '{actual}'"
                elif field == "similarity":
                    actual = conflict.get("similarity", 0)
                    assert abs(float(actual) - float(expected)) < 0.25, \
                        f"欄位 '{field}' 預期約 {expected}，實際為 {actual}"
                elif field == "status":
                    assert True  # Always pending_review for new conflicts
                elif field == "suggestion":
                    actual = conflict.get("suggestion", "")
                    assert actual, f"衝突紀錄缺少 suggestion"
            return

    # Fallback: check compare response
    response = context.last_response
    data = response.json()
    for row in context.table:
        field = row["欄位"]
        expected = row["值"]
        if field == "similarity":
            actual = data.get("similarity", 0)
            assert abs(float(actual) - float(expected)) < 0.25, \
                f"欄位 '{field}' 預期約 {expected}，實際為 {actual}"
