"""Given 維修排程前置條件 — Aggregate Given"""

import uuid
from datetime import datetime, timezone

from behave import given

from app.models.maintenance_schedule import MaintenanceSchedule
from app.repositories.maintenance_schedule_repository import MaintenanceScheduleRepository


@given('當前維修排程的結束時間為 "{end_time}"')
def step_impl(context, end_time):
    repo = MaintenanceScheduleRepository(context.db_session)

    # Use first admin as created_by
    created_by_uuid = None
    for key, val in context.ids.items():
        if "@" in key:
            created_by_uuid = uuid.UUID(val)
            break

    ends_at = datetime.fromisoformat(end_time).replace(tzinfo=timezone.utc)

    schedule = MaintenanceSchedule(
        name="測試維修排程",
        status="active",
        starts_at=datetime.now(timezone.utc),
        ends_at=ends_at,
        is_full_site=True,
        created_by=created_by_uuid,
    )
    saved = repo.save(schedule)
    context.memo["current_schedule_id"] = str(saved.id)


@given('維修健康檢查已通過')
def step_health_check_passed(context):
    schedule_id = context.memo.get("current_schedule_id")
    if schedule_id:
        from app.models.maintenance_schedule import MaintenanceSchedule
        db = context.db_session
        schedule = db.query(MaintenanceSchedule).filter_by(
            id=uuid.UUID(schedule_id)
        ).first()
        if schedule:
            schedule.health_check_passed = True
            db.commit()
