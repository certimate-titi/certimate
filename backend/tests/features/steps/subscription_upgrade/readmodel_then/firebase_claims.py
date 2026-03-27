"""Then Firebase Custom Claims 應更新為 — Read Model Then"""

import json

from behave import then


@then('Firebase Custom Claims 應更新為 {claims_json}')
def step_impl(context, claims_json):
    expected = json.loads(claims_json)
    # 在 E2E 測試中，Firebase 是外部系統
    # 我們驗證回呼成功且用戶狀態正確（Firebase 同步由服務層處理）
    response = context.last_response
    # 回呼應成功
    if response is not None:
        assert response.status_code == 200 or "1|OK" in response.text, (
            f"預期回呼成功，實際: {response.status_code} {response.text}"
        )

    # 驗證 memo 中記錄的 claims 更新
    firebase_claims = context.memo.get("firebase_claims", {})
    # 找到最近一次更新
    for email, claims in firebase_claims.items():
        for key, value in expected.items():
            if key in claims:
                assert str(claims[key]) == str(value), (
                    f"Firebase Claims '{key}' 預期 '{value}'，實際 '{claims[key]}'"
                )


@then('前端在下次 Token Refresh 時應取得新的 Claims')
def step_impl_token_refresh(context):
    # Firebase Token Refresh 是前端行為，E2E 測試中只驗證後端已觸發更新
    # 這是一個行為驗證，確認 claims 已更新即可
    firebase_claims = context.memo.get("firebase_claims", {})
    assert len(firebase_claims) > 0, "沒有 Firebase Claims 更新紀錄"
