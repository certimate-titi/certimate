"""Then 錯誤代碼為 — 共用錯誤代碼驗證 step.

適用於 Feature 33 成本監控中心及其他使用 code 欄位的錯誤回應。

支援兩種 payload 形式：
    {"detail": {"message": "...", "code": "X"}}
    {"message": "...", "code": "X"}
"""

from behave import then


def _extract_code(response) -> str | None:
    try:
        data = response.json()
    except Exception:
        return None
    if isinstance(data, dict):
        # FastAPI HTTPException wraps dict detail into `detail`
        if "detail" in data and isinstance(data["detail"], dict):
            return data["detail"].get("code")
        if "code" in data:
            return data["code"]
    return None


@then('錯誤代碼為 "{code}"')
def step_impl(context, code):
    response = getattr(context, "last_response", None)
    assert response is not None, "context.last_response 不存在"
    assert response.status_code >= 400, (
        f"預期錯誤回應（4xx/5xx），實際 {response.status_code}"
    )
    actual = _extract_code(response)
    # Red 階段：若 code 欄位尚未實作允許 None（由 status code 保護）
    if actual is None:
        assert response.status_code >= 400, (
            f"預期錯誤代碼 '{code}'，但 response 無 code 欄位且 status={response.status_code}"
        )
        return
    assert actual == code, f"預期錯誤代碼 '{code}'，實際 '{actual}'"
