"""Then 扣除該用戶本月 {count} 次的高階教練解題額度 — Read Model"""

from behave import then


@then('扣除該用戶本月 {count:d} 次的高階教練解題額度')
def quota_deducted(context, count):
    response = context.last_response
    assert response.status_code == 200, (
        f"預期 HTTP 200，實際 {response.status_code}: {response.text}"
    )

    data = response.json()
    assert "quota_used" in data, (
        f"回應缺少 'quota_used' 欄位，實際欄位: {list(data.keys())}"
    )
    assert data["quota_used"] == count, (
        f"預期 quota_used == {count}，實際: {data['quota_used']}"
    )
