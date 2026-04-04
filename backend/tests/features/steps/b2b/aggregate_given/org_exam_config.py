"""Given 系統中有以下機構考卷設定 — Aggregate Given"""

import uuid

from behave import given


@given('系統中有以下機構考卷設定：')
def step_impl(context):
    """Store org exam configs in memo for later use."""
    for row in context.table:
        exam_id = int(row["考卷 ID"])
        inst_id = int(row["機構 ID"])
        name = row["名稱"]
        status = row["狀態"].strip()

        context.memo[f"org_exam_{exam_id}"] = {
            "id": exam_id,
            "institution_id": inst_id,
            "name": name,
            "status": status,
        }
        context.ids[f"org_exam_{exam_id}"] = str(uuid.UUID(int=exam_id))
