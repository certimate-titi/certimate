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
        stage_order = int(row["順序"])
        status = row["狀態"]

        template = PromptTemplate(
            id=uuid.UUID(int=stage_id),
            stage_name=stage_name,
            stage_order=stage_order,
            status=status,
            content=f"預設 {stage_name} Prompt 模板內容",
            version=1,
            modified_by="admin@certimate.com",
            modified_at=datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        db.add(template)
        context.ids[f"prompt_template_{stage_id}"] = str(template.id)

        # Also create initial history
        history = PromptTemplateHistory(
            template_id=template.id,
            version=1,
            content=template.content,
            modified_by="admin@certimate.com",
            modified_at=datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
        )
        db.add(history)

    db.commit()
