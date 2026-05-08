"""SM-2 spaced repetition service — Sprint 5 P4 (T44).

實作 SuperMemo SM-2 演算法（per https://en.wikipedia.org/wiki/SuperMemo）。

UX 對應：
    用戶 RetrievalCard 點「沒想到 / 想到一半 / 完全想到」自評
    → scaffold_interaction_log 寫入 (recall_quality: none|partial|full)
    → SM-2 service 把 quality 轉成 SM-2 grade (0-5)
    → 計算 ease_factor / interval_days / repetitions / next_review_at
    → 寫入 scaffold_review_schedule

T44 範圍：
    - 演算法 + DB 寫入函式
    - update_review() 公開 API
    - 不接 endpoint（T45 接）
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scaffold_review_schedule import ScaffoldReviewSchedule

logger = logging.getLogger(__name__)


# SM-2 演算法常數（per Wikipedia）
DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3


# scaffold interaction log recall_quality → SM-2 grade（0-5）
# 我們只用 3 種 quality（none/partial/full），對應 SM-2 0-5 中的 1/3/5
QUALITY_TO_SM2_GRADE: dict[str, int] = {
    "none": 1,     # 完全沒想到 → "complete blackout" 式失敗
    "partial": 3,  # 想到一半 → "correct response after hesitation"
    "full": 5,     # 完全想到 → "perfect response"
}


def _calc_next(
    grade: int,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
) -> tuple[float, int, int]:
    """SM-2 核心演算法。

    Args:
        grade: 自評等級 0-5
        ease_factor: 當前記憶因子
        interval_days: 當前間隔
        repetitions: 連續答對次數

    Returns:
        (new_ease_factor, new_interval_days, new_repetitions)
    """
    # 1) 更新 ease_factor
    new_ef = ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if new_ef < MIN_EASE_FACTOR:
        new_ef = MIN_EASE_FACTOR

    # 2) 答錯（grade < 3）→ 重置 repetitions = 0, interval = 1
    if grade < 3:
        return new_ef, 1, 0

    # 3) 答對 → repetitions + 1, interval 依 SM-2 公式
    new_reps = repetitions + 1
    if new_reps == 1:
        new_interval = 1
    elif new_reps == 2:
        new_interval = 6
    else:
        new_interval = round(interval_days * new_ef)

    return new_ef, new_interval, new_reps


def update_review(
    db: Session,
    user_id: UUID,
    scaffold_id: UUID,
    recall_quality: str,
) -> ScaffoldReviewSchedule:
    """記錄一次自評 + 更新 SM-2 排程。

    Args:
        db: SQLAlchemy session
        user_id: 使用者
        scaffold_id: 鷹架
        recall_quality: "none" | "partial" | "full"

    Returns:
        更新後的 ScaffoldReviewSchedule（無則新建）

    Raises:
        ValueError: recall_quality 不合法
    """
    if recall_quality not in QUALITY_TO_SM2_GRADE:
        raise ValueError(
            f"invalid recall_quality '{recall_quality}'; expected one of "
            f"{list(QUALITY_TO_SM2_GRADE.keys())}"
        )
    grade = QUALITY_TO_SM2_GRADE[recall_quality]

    # Find or create schedule row
    sched = db.execute(
        select(ScaffoldReviewSchedule)
        .where(ScaffoldReviewSchedule.user_id == user_id)
        .where(ScaffoldReviewSchedule.scaffold_id == scaffold_id)
    ).scalar_one_or_none()

    if sched is None:
        sched = ScaffoldReviewSchedule(
            user_id=user_id,
            scaffold_id=scaffold_id,
            ease_factor=DEFAULT_EASE_FACTOR,
            interval_days=1,
            repetitions=0,
            next_review_at=datetime.now(timezone.utc),
        )
        db.add(sched)
        db.flush()

    new_ef, new_interval, new_reps = _calc_next(
        grade=grade,
        ease_factor=float(sched.ease_factor),
        interval_days=int(sched.interval_days),
        repetitions=int(sched.repetitions),
    )

    sched.ease_factor = new_ef
    sched.interval_days = new_interval
    sched.repetitions = new_reps
    sched.last_reviewed_at = datetime.now(timezone.utc)
    sched.next_review_at = datetime.now(timezone.utc) + timedelta(days=new_interval)
    db.flush()

    logger.info(
        "[sm2] scaffold=%s quality=%s grade=%d → ef=%.2f interval=%d days reps=%d",
        scaffold_id, recall_quality, grade, new_ef, new_interval, new_reps,
    )
    return sched


def list_due_reviews(
    db: Session,
    user_id: UUID,
    limit: int = 20,
) -> list[ScaffoldReviewSchedule]:
    """取「今日該複習」清單（next_review_at <= now）。

    Args:
        db: SQLAlchemy session
        user_id: 使用者
        limit: 上限（default 20）

    Returns:
        ScaffoldReviewSchedule 清單，按 next_review_at 升序
    """
    now = datetime.now(timezone.utc)
    return list(db.execute(
        select(ScaffoldReviewSchedule)
        .where(ScaffoldReviewSchedule.user_id == user_id)
        .where(ScaffoldReviewSchedule.next_review_at <= now)
        .order_by(ScaffoldReviewSchedule.next_review_at.asc())
        .limit(limit)
    ).scalars().all())
