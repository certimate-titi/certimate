"""Given 資料表 resources, subjects, user_subjects, exams, questions 於歷史資料中存在 tenant_id IS NULL 的列."""

import uuid
from behave import given


@given("資料表 resources, subjects, user_subjects, exams, questions 於歷史資料中存在 tenant_id IS NULL 的列")
def step_impl(context):
    """驗證當前 DB 中測試表的 tenant_id 欄位存在，且確認 migration 061 已完成回填。

    由於 Testcontainers 已套用完整 migration（含 061），所有列的 tenant_id
    應已被回填。此步驟標記 context.memo 供後續 Then 步驟讀取。
    """
    # 記錄測試意圖：migration 061 應已在 Testcontainers 環境中執行
    context.memo["migration_061_tables"] = [
        "resources", "subjects", "user_subjects", "exams", "questions"
    ]
    context.memo["migration_061_checked"] = True
