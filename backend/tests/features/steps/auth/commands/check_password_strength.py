"""When 密碼強度檢查 — 純前端計算（鏡射 frontend/app/signup/page.tsx:155-167）。

決策紀錄：2026-04-24 CEO 裁決 B1→α，密碼強度指示條為純前端計算，
step 不呼叫後端 API；若後續確認 `/auth/password-strength` 無其他依賴可刪。
"""

from behave import when


def _compute_password_strength(password: str) -> str:
    if len(password) == 0:
        return ""
    if len(password) < 8:
        return "弱"
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    trait_count = sum([has_upper, has_lower, has_digit])
    if trait_count == 3:
        return "強"
    if trait_count >= 2:
        return "中"
    return "弱"


@when('使用者輸入密碼 "{password}"')
def step_impl(context, password):
    context.memo["password_strength_label"] = _compute_password_strength(password)
