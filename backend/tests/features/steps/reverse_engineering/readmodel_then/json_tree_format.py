"""Then 回應格式應為巢狀 JSON — ReadModel Then"""

from behave import then


@then('回應格式應為巢狀 JSON：')
def step_impl(context):
    response = context.last_response
    assert response.status_code in [200, 201], \
        f"預期成功，實際 {response.status_code}: {response.text}"

    data = response.json()
    tree = data.get("tree", data.get("children", data))

    # Validate expected fields from DataTable
    expected_fields = {row["欄位"]: row["型別"] for row in context.table}

    def _validate_node(node):
        for field, field_type in expected_fields.items():
            assert field in node, \
                f"節點缺少欄位 '{field}'，實際欄位：{list(node.keys())}"

            # Basic type checks
            if field_type == "string (uuid)":
                assert isinstance(node[field], str), \
                    f"欄位 '{field}' 預期為 string，實際為 {type(node[field])}"
            elif field_type == "string":
                assert isinstance(node[field], str), \
                    f"欄位 '{field}' 預期為 string，實際為 {type(node[field])}"
            elif field_type == "integer":
                assert isinstance(node[field], int), \
                    f"欄位 '{field}' 預期為 integer，實際為 {type(node[field])}"
            elif field_type == "array":
                assert isinstance(node[field], list), \
                    f"欄位 '{field}' 預期為 array，實際為 {type(node[field])}"
            elif field_type == "object":
                assert isinstance(node[field], dict), \
                    f"欄位 '{field}' 預期為 object，實際為 {type(node[field])}"

        # Recurse into children
        for child in node.get("children", []):
            _validate_node(child)

    if isinstance(tree, list):
        for node in tree:
            _validate_node(node)
    else:
        _validate_node(tree)
