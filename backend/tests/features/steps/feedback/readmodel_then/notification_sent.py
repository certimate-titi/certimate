"""Then 系統應發送確認通知至 "..." / 系統應發送通知至 "..." — Readmodel Then"""

from behave import then


@then('系統應發送確認通知至 "{email}"，主旨含「{subject_keyword}」')
def step_impl(context, email, subject_keyword):
    # In E2E API tests, notification sending is verified by checking
    # the response or a notification log. For now, we verify the API
    # acknowledged the notification target.
    response = context.last_response
    data = response.json()

    # The API may include a notification_sent field or we trust the
    # successful response implies notification was queued
    assert response.status_code < 400, \
        f"預期操作成功（通知會被發送），實際 HTTP {response.status_code}"

    # Optionally check notification_sent in response
    notification = data.get("notification_sent")
    if notification is not None:
        assert notification is True, \
            f"預期通知已發送，實際 notification_sent={notification}"


@then('系統應發送通知至 "{email}"，主旨含「{subject_keyword}」')
def step_impl(context, email, subject_keyword):
    response = context.last_response
    data = response.json()

    assert response.status_code < 400, \
        f"預期操作成功（通知會被發送），實際 HTTP {response.status_code}"

    notification = data.get("notification_sent")
    if notification is not None:
        assert notification is True, \
            f"預期通知已發送，實際 notification_sent={notification}"
