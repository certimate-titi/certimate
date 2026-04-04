"""When 使用者選擇以下備考科目並設定 — Command (POST)"""

from behave import when


@when('使用者選擇以下備考科目並設定：')
def step_impl(context):
    token = context.memo.get("current_token")

    subjects = []
    for row in context.table:
        entry = {
            "subject_name": row["科目"],
            "exam_date": row["預計考試日期"],
            "self_assessed_level": row["自評程度"],
        }
        if "預計放榜日期" in row.headings:
            entry["result_date"] = row["預計放榜日期"]
        subjects.append(entry)

    response = context.api_client.post(
        "/api/v1/onboarding/subjects",
        headers={"Authorization": f"Bearer {token}"},
        json={"subjects": subjects},
    )
    context.last_response = response
