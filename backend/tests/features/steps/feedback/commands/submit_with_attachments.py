"""When 使用者 "..." 提交意見反饋時附加 N 張... — Command (POST)"""

from behave import when


@when('使用者 "{email}" 提交意見反饋時附加 {count:d} 張 PNG 截圖，各 {size_mb:d} MB')
def step_impl(context, email, count, size_mb):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    attachments = []
    for i in range(count):
        attachments.append({
            "filename": f"screenshot_{i + 1}.png",
            "file_size": size_mb * 1024 * 1024,
            "mime_type": "image/png",
            "file_path": f"/uploads/feedback/screenshot_{i + 1}.png",
        })

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "BUG",
            "subject": "附件測試主旨",
            "content": "附件測試內容",
            "attachments": attachments,
        },
    )
    context.last_response = response


@when('使用者 "{email}" 提交意見反饋時附加 {count:d} 張 {size_mb:d} MB 的 PNG 截圖')
def step_impl_oversize(context, email, count, size_mb):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    attachments = []
    for i in range(count):
        attachments.append({
            "filename": f"screenshot_{i + 1}.png",
            "file_size": size_mb * 1024 * 1024,
            "mime_type": "image/png",
            "file_path": f"/uploads/feedback/screenshot_{i + 1}.png",
        })

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "BUG",
            "subject": "附件測試主旨",
            "content": "附件測試內容",
            "attachments": attachments,
        },
    )
    context.last_response = response


@when('使用者 "{email}" 提交意見反饋時附加 {count:d} 張截圖')
def step_impl_too_many(context, email, count):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    attachments = []
    for i in range(count):
        attachments.append({
            "filename": f"screenshot_{i + 1}.png",
            "file_size": 1024,
            "mime_type": "image/png",
            "file_path": f"/uploads/feedback/screenshot_{i + 1}.png",
        })

    response = context.api_client.post(
        "/api/v1/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "BUG",
            "subject": "附件測試主旨",
            "content": "附件測試內容",
            "attachments": attachments,
        },
    )
    context.last_response = response
