"""Analytics events collector — PRD-046 Sprint 2 stub.

Stateless log-only endpoint. Accepts batched events from the frontend
localStorage queue, logs them server-side. No DB persistence yet.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id

router = APIRouter(prefix="/analytics", tags=["analytics"])
log = logging.getLogger("analytics.events")

MAX_BATCH_SIZE = 200


class AnalyticsEvent(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    ts: int
    props: dict[str, Any] | None = None


class AnalyticsBatch(BaseModel):
    events: list[AnalyticsEvent] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


@router.post("/events")
def ingest_events(
    batch: AnalyticsBatch,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    if len(batch.events) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=413, detail={"message": "批次過大"})
    for ev in batch.events:
        log.info(
            "analytics.event",
            extra={
                "user_id": user_id,
                "event": ev.name,
                "ts": ev.ts,
                "props": ev.props or {},
            },
        )
    return {"ok": True, "accepted": len(batch.events)}
