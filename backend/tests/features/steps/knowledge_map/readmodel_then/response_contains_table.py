"""Then 回應應包含（DataTable 驗證）— ReadModel Then"""

from behave import then


@then('回應應包含：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    headings = context.table.headings

    # 格式 1: knowledge_map 用 "區塊" / "寬度比例" / "內容"
    if "區塊" in headings:
        for row in context.table:
            section = row['區塊']
            width = row['寬度比例']
            content = row['內容']

            assert section in data, f"回應中缺少區塊 '{section}'"
            section_data = data[section]
            assert section_data.get("width") == width, (
                f"區塊 '{section}' 寬度應為 '{width}'，但得到 '{section_data.get('width')}'"
            )
            assert content in section_data.get("content", ""), (
                f"區塊 '{section}' 內容應包含 '{content}'"
            )

    # 格式 2: "欄位" / "值"
    elif "欄位" in headings and "值" in headings:
        for row in context.table:
            field = row["欄位"]
            expected_value = row["值"]
            actual_value = data.get(field)
            assert actual_value is not None, \
                f"回應缺少欄位 '{field}'，實際回應: {list(data.keys())}"

            if expected_value.startswith("（"):
                assert actual_value is not None and str(actual_value).strip() != "", \
                    f"欄位 '{field}' 應非空白，實際為 '{actual_value}'"
            else:
                assert str(actual_value) == expected_value, \
                    f"欄位 '{field}' 預期為 '{expected_value}'，實際為 '{actual_value}'"

    # 格式 3: "欄位" / "說明" — 只驗證欄位存在
    elif "欄位" in headings and "說明" in headings:
        for row in context.table:
            field = row["欄位"]
            actual_value = data.get(field)
            assert actual_value is not None, \
                f"回應缺少欄位 '{field}'，實際回應: {list(data.keys())}"
