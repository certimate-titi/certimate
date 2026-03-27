"""Then 顏色規則驗證 — ReadModel Then"""

from behave import then


@then('顏色規則為：green >= 80、orange 60-79、red < 60、gray 未作答')
def step_impl(context):
    response = context.last_response
    data = response.json()

    nodes = data.get("nodes", [])
    for node in nodes:
        rate = node.get("mastery_rate", None)
        color = node.get("color", "")

        if rate is None or rate == 0:
            # 未作答應為 gray（但 rate=0 也可能是真的 0 分）
            # 用 total_count 判斷是否未作答
            total = node.get("total_count", 0)
            if total == 0:
                assert color == "gray", (
                    f"未作答節點 '{node.get('name')}' 顏色應為 'gray'，但得到 '{color}'"
                )
        elif rate >= 80:
            assert color == "green", (
                f"答對率 {rate}% 的節點 '{node.get('name')}' 顏色應為 'green'，但得到 '{color}'"
            )
        elif rate >= 60:
            assert color == "orange", (
                f"答對率 {rate}% 的節點 '{node.get('name')}' 顏色應為 'orange'，但得到 '{color}'"
            )
        else:
            assert color == "red", (
                f"答對率 {rate}% 的節點 '{node.get('name')}' 顏色應為 'red'，但得到 '{color}'"
            )
