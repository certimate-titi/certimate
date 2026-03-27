"""Then step: Email 語氣應為溫馨風格，不含施壓或貶低用語"""

from behave import then


NEGATIVE_WORDS = ["懶", "差勁", "不及格", "必須", "警告", "立刻", "趕快", "否則"]


@then('Email 語氣應為溫馨風格，不含施壓或貶低用語')
def step_impl(context):
    notification = context.memo.get("last_notification", {})
    tone = notification.get("tone", "")
    body = notification.get("body", "")

    # Tone should be warm
    assert tone == "warm", f"Expected warm tone, got: {tone}"

    # Body should not contain negative/pressuring words
    for word in NEGATIVE_WORDS:
        assert word not in body, f"Body contains negative word '{word}': {body}"
