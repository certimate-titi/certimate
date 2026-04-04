"""Then step: Email 應包含「回到平台繼續學習」的 CTA 連結"""

from behave import then


@then('Email 應包含「回到平台繼續學習」的 CTA 連結')
def step_impl(context):
    email = context.memo.get("last_weekly_email", {})
    body = email.get("body", {})
    cta_text = body.get("cta_text", "")
    cta_url = body.get("cta_url", "")
    assert "回到平台繼續學習" in cta_text, \
        f"CTA text missing '回到平台繼續學習': {cta_text}"
    assert cta_url.startswith("http"), \
        f"CTA URL is not a valid URL: {cta_url}"
