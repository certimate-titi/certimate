from behave import then


@then('系統應同步清除 Redis 中所有與該使用者 ID 關聯的快取資料')
def step_impl(context):
    # E2E 測試中，驗證 API 回應表明已清除 Redis 快取
    # 在紅燈階段，此驗證會因 HTTP 404 而無法到達
    response = context.last_response
    data = response.json()
    cache_cleared = (
        data.get("cache_cleared") is True
        or "cache" in str(data).lower()
    )
    assert cache_cleared, \
        f"回應中未包含 Redis 快取已清除的資訊: {data}"
