"""Given 系統中有以下異常紀錄 — Aggregate Given"""

from datetime import datetime, timezone

from behave import given

from app.models.anomaly_record import AnomalyRecord
from app.repositories.anomaly_record_repository import AnomalyRecordRepository


@given('系統中有以下異常紀錄：')
def step_impl(context):
    repo = AnomalyRecordRepository(context.db_session)

    for row in context.table:
        record = AnomalyRecord(
            error_id=row["異常 ID"],
            error_type=row["錯誤類型"],
            occurrence_count=int(row["發生次數"]),
            status=row["狀態"].strip(),
            impact_scope=row["影響範圍"],
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        saved = repo.save(record)
        context.ids[row["異常 ID"]] = str(saved.id)
