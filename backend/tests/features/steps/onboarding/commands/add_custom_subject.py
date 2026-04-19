"""When 使用者在自訂科目輸入欄輸入名稱並點擊新增 — Command

Onboarding Step 2 的「已選科目」屬於前端尚未提交的暫存狀態，
此 step 以 context.memo 操作，不呼叫後端（無 /onboarding/subjects/custom endpoint）。
提交會在 `使用者點擊「完成並啟動學習歷程」` 時統一呼叫 POST /onboarding/subjects。
"""

from behave import when


def _fake_resp(context, status, payload):
    data = payload
    context.last_response = type(
        "FakeResp", (), {
            "status_code": status,
            "json": lambda self: data,
            "text": str(data),
        },
    )()


@when('使用者在自訂科目輸入欄輸入 "{subject_name}" 並點擊新增')
def step_impl(context, subject_name):
    selected = context.memo.setdefault("onboarding_selected_subjects", [])
    existing_names = {s["subject_name"] for s in selected}
    if subject_name in existing_names:
        _fake_resp(context, 400, {"message": "此科目已存在，請勿重複新增"})
        return
    entry = {
        "subject_name": subject_name,
        "is_custom": True,
        "self_assessed_level": "beginner",
    }
    selected.append(entry)
    context.memo["last_custom_subject"] = subject_name
    _fake_resp(context, 200, entry)
