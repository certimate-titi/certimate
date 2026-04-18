"""When 使用者切換已選科目的自評程度 — Command

Onboarding Step 2 的「已選科目」為前端暫存狀態，此 step 操作 context.memo。
實際提交透過 POST /onboarding/subjects 於流程結束時進行。
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


@when('使用者將 "{subject}" 的自評程度切換為 "{level}"')
def step_impl(context, subject, level):
    selected = context.memo.setdefault("onboarding_selected_subjects", [])
    for s in selected:
        if s.get("subject_name") == subject:
            s["self_assessed_level"] = level
            context.memo["last_subject_level_update"] = {"subject": subject, "level": level}
            _fake_resp(context, 200, s)
            return
    _fake_resp(context, 404, {"message": f"'{subject}' 未在已選科目列表中"})
