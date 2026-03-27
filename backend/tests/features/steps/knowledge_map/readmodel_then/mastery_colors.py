"""Then 節點應依答對率顯示顏色 — ReadModel Then"""

from behave import then


@then('節點應依答對率顯示顏色：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    nodes = data.get("nodes", [])

    for row in context.table:
        expected_name = row['名稱']
        expected_rate = int(row['答對率'])
        expected_color = row['顏色']

        found = False
        for node in nodes:
            if node.get("name") == expected_name:
                found = True
                actual_rate = node.get("mastery_rate", 0)
                actual_color = node.get("color", "")
                assert int(actual_rate) == expected_rate, (
                    f"節點 '{expected_name}' 答對率應為 {expected_rate}，但得到 {actual_rate}"
                )
                assert actual_color == expected_color, (
                    f"節點 '{expected_name}' 顏色應為 '{expected_color}'，但得到 '{actual_color}'"
                )
                break

        assert found, f"找不到節點 '{expected_name}' 在回應中"
