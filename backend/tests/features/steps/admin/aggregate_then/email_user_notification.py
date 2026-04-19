"""Then 系統應發送停權/恢復通知信 — 驗證 AdminService._send_email spy 紀錄"""

from behave import then

from app.models.user import User


def _resolve_email(context, target):
    """將 '使用者 5' 或 email 字串轉為 email。"""
    target = target.strip()
    if target.startswith("使用者 "):
        user_key = target.split("使用者 ", 1)[1].strip()
        user_id = context.ids.get(user_key)
        if user_id:
            user = context.db_session.query(User).filter(User.id == user_id).first()
            if user:
                return user.email
        return None
    return target


@then('系統應向使用者 {user_key} 發送停權通知信，原因包含 "{reason}"')
def step_suspend_email_with_reason(context, user_key, reason):
    email = _resolve_email(context, f"使用者 {user_key}")
    assert email, f"找不到使用者 {user_key} 的 email"
    matches = [
        e for e in context.sent_emails
        if e["method"] == "send_suspension_email"
        and e["args"]
        and e["args"][0] == email
        and reason in (e["args"][1] if len(e["args"]) > 1 else "")
    ]
    assert matches, (
        f"未發送停權通知信給 {email}（原因含 '{reason}'）。"
        f"實際 sent_emails={context.sent_emails}"
    )


@then('系統應向 "{email}" 發送帳號恢復通知信')
def step_restoration_email(context, email):
    matches = [
        e for e in context.sent_emails
        if e["method"] == "send_restoration_email"
        and e["args"] and e["args"][0] == email
    ]
    assert matches, (
        f"未發送帳號恢復通知信給 {email}。實際 sent_emails={context.sent_emails}"
    )
