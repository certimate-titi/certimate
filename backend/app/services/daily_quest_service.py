"""DailyQuestService — daily quest progress tracking.

Quest definitions are declared as code (no DB table), with per-user, per-day
progress persisted to `daily_quest_progress`.

Quest keys:
- `practice_nodes` — practice distinct knowledge nodes today (target: 3)
- `complete_exam`  — submit at least one exam today (target: 1)
"""

from __future__ import annotations

import uuid
from datetime import date as date_type, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.daily_quest_progress import DailyQuestProgress


QUEST_DEFS: dict[str, dict[str, Any]] = {
    "practice_nodes": {
        "id": "q1",
        "type": "review",
        "quest_type": "review",
        "title": "練習 3 個知識節點",
        "tooltip": "從知識圖譜選擇節點進行練習，不同節點各計 1 次",
        "target": 3,
    },
    "complete_exam": {
        "id": "q2",
        "type": "quiz",
        "quest_type": "quiz",
        "title": "完成一份模擬測驗",
        "tooltip": "提交一份模擬考卷即可達成",
        "target": 1,
    },
}

# Map public quest id -> internal key
_ID_TO_KEY = {d["id"]: k for k, d in QUEST_DEFS.items()}


def _today() -> date_type:
    return datetime.now(timezone.utc).date()


class DailyQuestService:
    def __init__(self, db: Session):
        self.db = db

    # ── Internal ──────────────────────────────────────────────────────

    def _get_or_create(self, user_id: uuid.UUID, quest_key: str) -> DailyQuestProgress:
        d = QUEST_DEFS[quest_key]
        today = _today()
        row = (
            self.db.query(DailyQuestProgress)
            .filter_by(user_id=user_id, quest_date=today, quest_key=quest_key)
            .first()
        )
        if row:
            return row
        row = DailyQuestProgress(
            user_id=user_id,
            quest_date=today,
            quest_key=quest_key,
            progress=0,
            target=int(d["target"]),
            meta=None,
        )
        self.db.add(row)
        self.db.flush()
        return row

    # ── Public — increment/record ─────────────────────────────────────

    def record_node_practiced(self, user_id: str, node_id: str) -> DailyQuestProgress | None:
        """Practice hook: count distinct node_ids per day toward `practice_nodes`."""
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return None
        row = self._get_or_create(uid, "practice_nodes")
        if row.completed_at is not None:
            return row
        seen = set((row.meta or {}).get("node_ids", []))
        if node_id in seen:
            return row
        seen.add(node_id)
        row.meta = {"node_ids": sorted(seen)}
        row.progress = min(len(seen), row.target)
        if row.progress >= row.target and row.completed_at is None:
            row.completed_at = datetime.now(timezone.utc)
        return row

    def record_exam_completed(self, user_id: str, exam_id: str) -> DailyQuestProgress | None:
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return None
        row = self._get_or_create(uid, "complete_exam")
        if row.completed_at is not None:
            return row
        seen = set((row.meta or {}).get("exam_ids", []))
        if exam_id in seen:
            return row
        seen.add(exam_id)
        row.meta = {"exam_ids": sorted(seen)}
        row.progress = min(len(seen), row.target)
        if row.progress >= row.target and row.completed_at is None:
            row.completed_at = datetime.now(timezone.utc)
        return row

    # ── Public — query ────────────────────────────────────────────────

    def list_today(self, user_id: str) -> list[dict]:
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return []
        today = _today()
        rows = {
            r.quest_key: r
            for r in self.db.query(DailyQuestProgress).filter_by(user_id=uid, quest_date=today).all()
        }
        result = []
        for key, d in QUEST_DEFS.items():
            row = rows.get(key)
            progress = row.progress if row else 0
            target = int(d["target"])
            completed = bool(row and row.completed_at)
            result.append({
                "id": d["id"],
                "type": d["type"],
                "quest_type": d["quest_type"],
                "title": d["title"],
                "tooltip": d["tooltip"],
                "progress": progress,
                "target": target,
                "status": "completed" if completed else "pending",
                "completed_at": row.completed_at.isoformat() if (row and row.completed_at) else None,
            })
        return result

    def mark_complete_by_id(self, user_id: str, quest_public_id: str) -> dict | None:
        """Legacy manual completion (frontend may still call this)."""
        key = _ID_TO_KEY.get(quest_public_id)
        if not key:
            return None
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, TypeError):
            return None
        row = self._get_or_create(uid, key)
        if row.completed_at is None:
            row.progress = row.target
            row.completed_at = datetime.now(timezone.utc)
        return {
            "id": quest_public_id,
            "progress": row.progress,
            "target": row.target,
            "status": "completed",
        }
