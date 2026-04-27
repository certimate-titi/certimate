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

            assert field in data, \
                f"回應缺少欄位 '{field}'，實際回應: {list(data.keys())}"
            actual_value = data[field]

            if expected_value == "null":
                assert actual_value is None, \
                    f"欄位 '{field}' 預期為 null，實際為 '{actual_value}'"
            elif expected_value.startswith("（"):
                assert actual_value is not None and str(actual_value).strip() != "", \
                    f"欄位 '{field}' 應非空白，實際為 '{actual_value}'"
            else:
                # Try direct string comparison first
                if str(actual_value) == expected_value:
                    pass  # match
                elif (
                    hasattr(context, 'ids')
                    and expected_value in context.ids
                    and field.endswith("_id")
                ):
                    # Only resolve via context.ids for fields ending with _id
                    assert str(actual_value) == context.ids[expected_value], \
                        f"欄位 '{field}' 預期為 '{expected_value}' (UUID: {context.ids[expected_value]})，實際為 '{actual_value}'"
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

    # 格式 4: "欄位" / "預期值" — Feature 33 async import (smart match)
    elif "欄位" in headings and "預期值" in headings:
        import uuid as _uuid
        for row in context.table:
            field = row["欄位"]
            spec = row["預期值"]
            value = data.get(field) if isinstance(data, dict) else None

            if "非空" in spec or "UUID" in spec:
                assert value, f"Field '{field}' should be non-empty, got {value}"
                if "UUID" in spec:
                    try:
                        _uuid.UUID(str(value))
                    except (ValueError, AttributeError):
                        raise AssertionError(f"Field {field}={value} is not a UUID")
            elif spec.startswith('"') and spec.endswith('"'):
                expected = spec.strip('"')
                assert value == expected, f"Field {field}: expected {expected!r}, got {value!r}"
            elif "包含" in spec:
                needle = spec.replace("包含", "").strip().strip('"')
                assert isinstance(value, str) and needle.lower() in value.lower(), (
                    f"Expected '{needle}' in {field}={value!r}"
                )
            else:
                assert field in data, f"Field '{field}' missing from response"

    # 格式 5: "欄位" / "含義" — informational; just check existence (deep)
    elif "欄位" in headings and "含義" in headings:
        def _deep_has_key(payload, key):
            if isinstance(payload, dict):
                if key in payload:
                    return True
                return any(_deep_has_key(v, key) for v in payload.values())
            if isinstance(payload, list):
                return any(_deep_has_key(v, key) for v in payload)
            return False
        for row in context.table:
            field = row["欄位"]
            assert _deep_has_key(data, field), \
                f"Field '{field}' missing from response: {list(data.keys()) if isinstance(data, dict) else data}"

    # 格式 6: "項目" / "內容" — dashboard top-level keys (existence check, deep)
    elif "項目" in headings and "內容" in headings:
        def _deep_has_key6(payload, key):
            if isinstance(payload, dict):
                if key in payload:
                    return True
                return any(_deep_has_key6(v, key) for v in payload.values())
            if isinstance(payload, list):
                return any(_deep_has_key6(v, key) for v in payload)
            return False
        for row in context.table:
            field = row["項目"]
            assert _deep_has_key6(data, field), f"Missing field '{field}' in response"

    # 格式 7: "指標" / "說明" — performance-metrics
    elif "指標" in headings and "說明" in headings:
        def _deep_has_key7(payload, key):
            if isinstance(payload, dict):
                if key in payload:
                    return True
                return any(_deep_has_key7(v, key) for v in payload.values())
            if isinstance(payload, list):
                return any(_deep_has_key7(v, key) for v in payload)
            return False
        for row in context.table:
            field = row["指標"]
            assert _deep_has_key7(data, field), f"Missing metric '{field}' in response"

    # 格式 8: "部分" / "內容" — job-details sections
    elif "部分" in headings and "內容" in headings:
        for row in context.table:
            section = row["部分"]
            assert section in data, f"Missing section '{section}' in response: {list(data.keys()) if isinstance(data, dict) else data}"
