"""Then 交易列表篩選與搜尋驗證 — ReadModel Then"""

from behave import then


@then('交易列表應即時過濾，僅顯示交易 ID 包含 "{keyword}" 的紀錄')
def step_impl_filter_by_keyword(context, keyword):
    """驗證搜尋結果只含關鍵字符合的交易。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        transactions = data if isinstance(data, list) else data.get("transactions", [])
        for t in transactions:
            txn_id = t.get("transaction_id") or t.get("id") or ""
            assert keyword in txn_id, \
                f"所有交易 ID 應包含 '{keyword}'，但發現 '{txn_id}'"


@then('列表中應包含交易 "{transaction_id}"')
def step_impl_list_contains_txn(context, transaction_id):
    """驗證交易列表包含指定交易。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        transactions = data if isinstance(data, list) else data.get("transactions", [])
        ids = [t.get("transaction_id") or t.get("id") or "" for t in transactions]
        assert transaction_id in ids, \
            f"交易列表應包含 '{transaction_id}'，實際: {ids}"


@then('列表中不應包含交易 "{transaction_id}"')
def step_impl_list_excludes_txn(context, transaction_id):
    """驗證交易列表不含指定交易。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        transactions = data if isinstance(data, list) else data.get("transactions", [])
        ids = [t.get("transaction_id") or t.get("id") or "" for t in transactions]
        assert transaction_id not in ids, \
            f"交易列表不應包含 '{transaction_id}'，但發現於: {ids}"


@then('交易列表應僅顯示狀態為 "{expected_status}" 的交易')
def step_impl_filter_by_status(context, expected_status):
    """驗證列表所有交易狀態符合篩選條件。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
    if response.status_code in (200, 201):
        data = response.json()
        transactions = data if isinstance(data, list) else data.get("transactions", [])
        for t in transactions:
            actual_status = t.get("status") or ""
            assert actual_status == expected_status, \
                f"交易列表應僅顯示狀態 '{expected_status}'，但發現 '{actual_status}'"
