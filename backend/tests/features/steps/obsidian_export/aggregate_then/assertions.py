"""Then assertions — Feature 53 Obsidian Export BDD."""

import io
import zipfile

from behave import then


@then("response content-type 為 application/zip")
def step_response_content_type_zip(context):
    content_type = context.last_response.headers.get("content-type", "")
    assert "application/zip" in content_type, (
        f"Expected application/zip, got: {content_type}"
    )


@then("response body 為非空 bytes")
def step_response_body_nonempty(context):
    body = context.last_response.content
    assert len(body) > 0, "Response body 為空"
    # 驗證可解開 ZIP
    buf = io.BytesIO(body)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
    assert isinstance(names, list), "ZIP 無法解析 namelist"


@then('response JSON 含 message "{expected_message}"')
def step_response_json_contains_message(context, expected_message):
    data = context.last_response.json()
    # FastAPI HTTPException detail 可能在 detail.message 或 detail 字串
    detail = data.get("detail", data)
    if isinstance(detail, dict):
        actual = detail.get("message", "")
    else:
        actual = str(detail)
    assert expected_message in actual, (
        f"Expected message '{expected_message}' in response, got: {actual}"
    )


@then("bob 的 ZIP 不含 alice 的筆記檔案")
def step_bob_zip_no_alice_notes(context):
    """bob 的 ZIP 應只含 bob 自己的 notes（bob 無 note → 只有 index.md）。"""
    body = context.last_response.content
    assert len(body) > 0, "Response body 為空"
    buf = io.BytesIO(body)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
    # bob 沒有建立 notes，ZIP 應只含 index.md（無其他 .md 檔）
    note_files = [n for n in names if n != "index.md"]
    assert len(note_files) == 0, (
        f"bob 的 ZIP 包含非 index.md 的檔案，可能含有 alice 的 notes: {note_files}"
    )
