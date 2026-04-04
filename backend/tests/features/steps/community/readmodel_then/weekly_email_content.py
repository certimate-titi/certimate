"""Then step: Email 內容應包含學習時數、完成考試數與 AI 生成摘要"""

from behave import then


@then('Email 內容應包含學習時數、完成考試數與 AI 生成摘要')
def step_impl(context):
    email = context.memo.get("last_weekly_email", {})
    body = email.get("body", {})
    assert "study_hours" in body, f"Email body missing study_hours: {body}"
    assert "exams_completed" in body, f"Email body missing exams_completed: {body}"
    assert "progress_summary" in body, f"Email body missing progress_summary: {body}"
    assert body["progress_summary"] and body["progress_summary"].strip(), \
        "progress_summary is empty"
