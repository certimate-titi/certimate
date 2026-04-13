"""Then 回應應包含 N 個分塊。"""

from behave import then


@then('回應應包含 {count:d} 個分塊')
def step_impl(context, count):
    data = context.last_response.json()
    chunks = data.get("chunks", [])
    assert len(chunks) == count, (
        f"預期 {count} 個分塊，實際得到 {len(chunks)} 個"
    )
