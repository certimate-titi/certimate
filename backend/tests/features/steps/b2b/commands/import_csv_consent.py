"""When 使用者上傳合法 CSV 進行學員匯入（含/不含個資同意） — Command"""

import io

from behave import when


def _dummy_csv():
    return "姓名,電子郵件,群組\n測試學生,consent_test@example.com,預設群組"


@when('使用者 "{email}" 上傳合法 CSV 進行學員匯入，但未勾選同意「學員資料處理條款」')
def step_impl_no_consent(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    csv_content = _dummy_csv()

    response = context.api_client.post(
        "/api/v1/b2b/students/import",
        files={"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        params={"consent_checked": False, "confirm_surcharge": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response


@when('使用者 "{email}" 上傳合法 CSV 進行學員匯入，並已勾選同意「學員資料處理條款」')
def step_impl_with_consent(context, email):
    user_id = context.ids[email]
    token = context.jwt_helper.generate_token(user_id)
    csv_content = _dummy_csv()

    response = context.api_client.post(
        "/api/v1/b2b/students/import",
        files={"file": ("students.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        params={"consent_checked": True, "confirm_surcharge": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    context.last_response = response
