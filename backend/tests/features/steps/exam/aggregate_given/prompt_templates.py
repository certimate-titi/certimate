"""Given 系統中有以下 AI Prompt 模板設定 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.prompt_template import PromptTemplate, PromptTemplateHistory


@given('系統中有以下 AI Prompt 模板設定：')
def step_impl(context):
    db = context.db_session

    for row in context.table:
        stage_id = int(row["階段 ID"])
        stage_name = row["階段名稱"]
        order = int(row["順序"])
        status = row["狀態"]

        template = PromptTemplate(
            id=uuid.UUID(int=stage_id),
            stage_name=stage_name,
            stage_order=order,
            status=status,
            content=f"更新版 {stage_name} Prompt 模板內容",
            version=2,
            modified_by="admin@certimate.com",
            modified_at=datetime(2026, 3, 26, 10, 0, 0, tzinfo=timezone.utc),
        )
        db.merge(template)

        # Create v1 history entry
        history_v1 = PromptTemplateHistory(
            template_id=template.id,
            version=1,
            content=f"預設 {stage_name} Prompt 模板內容",
            modified_by="admin@certimate.com",
            modified_at=datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        db.add(history_v1)

        # Create v2 history entry
        history_v2 = PromptTemplateHistory(
            template_id=template.id,
            version=2,
            content=f"更新版 {stage_name} Prompt 模板內容",
            modified_by="admin@certimate.com",
            modified_at=datetime(2026, 3, 26, 10, 0, 0, tzinfo=timezone.utc),
        )
        db.add(history_v2)

        context.ids[f"prompt_template_{stage_id}"] = str(template.id)

    db.commit()
