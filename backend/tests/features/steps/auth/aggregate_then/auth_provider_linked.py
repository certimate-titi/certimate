from behave import then
from app.repositories.user_repository import UserRepository


PROVIDER_MAP = {
    "Google SSO": "google",
    "email": "email",
}


@then('該帳號的註冊方式應允許或更新關聯 "{provider}"')
def step_impl(context, provider):
    response = context.last_response
    data = response.json()
    email = data.get("email") or data.get("user", {}).get("email")
    assert email is not None, f"回應中找不到 email 欄位: {data}"

    repo = UserRepository(context.db_session)
    context.db_session.expire_all()
    user = repo.find_by_email(email)
    assert user is not None, f"DB 中找不到 email='{email}' 的使用者"

    expected_provider = PROVIDER_MAP.get(provider, provider.lower())
    assert user.auth_provider == expected_provider or "google" in user.auth_provider, \
        f"auth_provider 應包含 '{expected_provider}'，實際為 '{user.auth_provider}'"
