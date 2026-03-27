"""Then 反饋紀錄應包含 N 個附件的儲存路徑 — Readmodel Then"""

from behave import then


@then('反饋紀錄應包含 {count:d} 個附件的儲存路徑')
def step_impl(context, count):
    response = context.last_response
    data = response.json()

    attachments = data.get("attachments", [])
    assert len(attachments) == count, \
        f"預期 {count} 個附件，實際 {len(attachments)} 個"

    for i, att in enumerate(attachments):
        # attachments 可能是字串列表或字典列表
        if isinstance(att, str):
            assert att.strip() != "", f"附件 {i + 1} 路徑為空"
        else:
            file_path = att.get("file_path") or att.get("path") or att.get("url")
            assert file_path is not None and str(file_path).strip() != "", \
                f"附件 {i + 1} 缺少儲存路徑，實際: {att}"
