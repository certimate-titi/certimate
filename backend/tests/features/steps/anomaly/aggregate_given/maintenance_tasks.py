"""Given 系統中有以下維修任務 — Aggregate Given"""

import uuid

from behave import given

from app.models.maintenance_task import MaintenanceTask
from app.repositories.maintenance_task_repository import MaintenanceTaskRepository


@given('系統中有以下維修任務：')
def step_impl(context):
    repo = MaintenanceTaskRepository(context.db_session)

    for row in context.table:
        # Resolve related_error_id from context.ids
        related_error_key = row["關聯異常"]
        related_error_uuid = None
        if related_error_key and related_error_key in context.ids:
            related_error_uuid = uuid.UUID(context.ids[related_error_key])

        # Use first available admin user as created_by
        created_by_uuid = None
        for key, val in context.ids.items():
            if "@" in key:
                created_by_uuid = uuid.UUID(val)
                break

        task = MaintenanceTask(
            task_id=row["任務 ID"],
            name=row["名稱"],
            priority=row["優先級"],
            related_error_id=related_error_uuid,
            status=row["狀態"],
            created_by=created_by_uuid,
        )
        saved = repo.save(task)
        context.ids[row["任務 ID"]] = str(saved.id)
