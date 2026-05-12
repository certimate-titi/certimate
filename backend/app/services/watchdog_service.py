"""Watchdog Service — dispatch timeout 自動標記失敗。

P0-1 hot-fix（Issue #68 v2）：
  Cloud Tasks dispatch silent fail 場景下，resource_parse_jobs 會停留在
  status=queued 永久不變，用戶端看到 PENDING。

  本 watchdog 每 1 分鐘掃一次：
    queued + created_at < now() - WATCHDOG_TIMEOUT_MINUTES（預設 10 分鐘）
    → 標記 parse_job.status = failed, failure_reason = 'dispatch timeout'
    → 同時標記 resource.status = FAILED

  冪等性保證：只掃 queued 狀態，已是 failed/success/parsing 一律跳過。
"""

import logging
import os
from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

logger = logging.getLogger("certimate.watchdog")

WATCHDOG_TIMEOUT_MINUTES = int(os.environ.get("WATCHDOG_TIMEOUT_MINUTES", "10"))


def run_dispatch_timeout_watchdog(db: Session) -> dict:
    """掃 queued parse_job 超過 WATCHDOG_TIMEOUT_MINUTES 的 rows，標記 FAILED。

    Args:
        db: SQLAlchemy sync Session（與 scheduler 共用 session_factory）

    Returns:
        {"marked": int}  — 本次標記數量

    冪等：相同 DB 狀態下重複呼叫結果一致，不重複標記。
    """
    from sqlalchemy import text
    from app.models.resource_parse_job import ResourceParseJob, ParseJobStatus
    from app.models.resource import Resource, ResourceStatus

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=WATCHDOG_TIMEOUT_MINUTES)

    stale_jobs = (
        db.query(ResourceParseJob)
        .filter(
            ResourceParseJob.status == ParseJobStatus.QUEUED,
            ResourceParseJob.created_at < cutoff,
        )
        .all()
    )

    if not stale_jobs:
        logger.debug("Watchdog: no stale queued jobs found (timeout=%d min)", WATCHDOG_TIMEOUT_MINUTES)
        return {"marked": 0}

    marked = 0
    resource_ids = []
    for job in stale_jobs:
        job.status = ParseJobStatus.FAILED
        job.failure_reason = "dispatch timeout"
        resource_ids.append(job.resource_id)
        marked += 1

    # 同步標記 resource FAILED
    if resource_ids:
        resources = (
            db.query(Resource)
            .filter(Resource.id.in_(resource_ids))
            .all()
        )
        for res in resources:
            # 只標記仍在 PENDING / PROCESSING 的 resource（避免覆蓋已手動成功的）
            if res.status in (ResourceStatus.PENDING, ResourceStatus.PROCESSING):
                res.status = ResourceStatus.FAILED

    db.commit()
    logger.warning(
        "Watchdog: marked %d stale parse_job(s) as FAILED (dispatch timeout > %d min)",
        marked,
        WATCHDOG_TIMEOUT_MINUTES,
    )
    return {"marked": marked}
