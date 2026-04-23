"""Analytics events collector — PRD-046 US-07.

Accepts batched events from the frontend localStorage queue and persists
them to `analytics_events`. Retention is expected to be enforced by an
external cron (90 days).
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_id, get_db
from app.models.analytics_event import AnalyticsEvent

router = APIRouter(prefix="/analytics", tags=["analytics"])

MAX_BATCH_SIZE = 200


class AnalyticsEventIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    ts: int
    props: dict[str, Any] | None = None


class AnalyticsBatch(BaseModel):
    events: list[AnalyticsEventIn] = Field(min_length=1, max_length=MAX_BATCH_SIZE)


@router.post("/events")
def ingest_events(
    batch: AnalyticsBatch,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    if len(batch.events) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=413, detail={"message": "批次過大"})

    uid = uuid.UUID(user_id)
    for ev in batch.events:
        db.add(AnalyticsEvent(
            user_id=uid,
            name=ev.name,
            props=ev.props,
            client_ts=ev.ts,
        ))
    db.commit()
    return {"ok": True, "accepted": len(batch.events)}
