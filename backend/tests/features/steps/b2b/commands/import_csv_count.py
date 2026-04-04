"""When 使用者上傳包含 N 名新學生的 CSV 進行學員匯入 — Command"""

import io
import uuid

from behave import when, use_step_matcher

use_step_matcher("re")


def _build_csv_for_count(count):
    """Generate a valid CSV with N dummy students."""
    lines = ["姓名,電子郵件,群組"]
    for i in range(count):
        lines.append(f"新學生{i+1},new_student_{i+1}_{uuid.uuid4().hex[:6]}@example.com,預設群組")
    return "\n".join(lines)


@when(r'使用者 "(?P<email>[^"]+)" 上傳包含 (?P<count>\d+) 名新學生的 CSV 進行學員匯入，並確認加購')
def step_impl_confirm(context, email, count):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    csv_content = _build_csv_for_count(int(count))

    response = context.api_client.post(
        "/api/v1/b2b/students/import",
        files={"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        params={"consent_checked": True, "confirm_surcharge": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when(r'使用者 "(?P<email>[^"]+)" 上傳包含 (?P<count>\d+) 名新學生的 CSV 進行學員匯入')
def step_impl(context, email, count):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    csv_content = _build_csv_for_count(int(count))

    response = context.api_client.post(
        "/api/v1/b2b/students/import",
        files={"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        params={"consent_checked": True, "confirm_surcharge": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


use_step_matcher("parse")
