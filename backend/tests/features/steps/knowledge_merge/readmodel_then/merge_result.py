"""Then 合併結果表格驗證 — ReadModel Then"""

from behave import then


@then('合併結果應為：')
def step_merge_result_table(context):
    response = context.last_response
    assert response.status_code == 200, \
        f"合併 API 失敗: {response.status_code} — {response.text}"
    data = response.json()

    merged_list = data.get("merged", [])
    added_list = data.get("added", [])

    for row in context.table:
        existing = row["既有節點"]
        incoming = row["教材節點"]
        action = row["合併動作"]

        if "語意匹配" in action or "合併" in action:
            # Should be in merged list
            matched = any(
                m.get("incoming_name") == incoming or m.get("existing_name") == existing
                for m in merged_list
            )
            assert matched, \
                f"教材節點 '{incoming}' 應出現在合併結果中，實際 merged: {merged_list}"
        elif "新增" in action:
            # Should be in added list
            matched = any(
                a.get("name") == incoming
                for a in added_list
            )
            assert matched, \
                f"教材節點 '{incoming}' 應出現在新增結果中，實際 added: {added_list}"
