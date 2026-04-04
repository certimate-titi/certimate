"""When 使用者上傳 CSV（表格）進行學員匯入 — Command"""

import io

from behave import when


@when('使用者 "{email}" 上傳以下合法 CSV 進行學員匯入：')
def step_impl(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    # Build CSV from table
    headers = context.table.headings
    lines = [",".join(headers)]
    for row in context.table:
        lines.append(",".join(row[h] for h in headers))
    csv_content = "\n".join(lines)

    response = context.api_client.post(
        "/api/v1/b2b/students/import",
        files={"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        params={"consent_checked": True, "confirm_surcharge": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 上傳以下 CSV 進行學員匯入：')
def step_impl_bad(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)

    headers = context.table.headings
    lines = [",".join(headers)]
    for row in context.table:
        lines.append(",".join(row[h] for h in headers))
    csv_content = "\n".join(lines)

    response = context.api_client.post(
        "/api/v1/b2b/students/import",
        files={"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        params={"consent_checked": True, "confirm_surcharge": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
