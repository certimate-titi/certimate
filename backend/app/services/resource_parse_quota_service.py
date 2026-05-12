"""Resource parse quota service — EPIC-035 M6 TASK-06.

檢查用戶本月可用 LLM 解析配額：
  FREE=5 / PRO=50 / PRO_PLUS=200 / ULTRA=-1（無限）

配額以日曆月計算（每月 1 日 00:00 UTC 重置）。
計量單位：該用戶當月 resource_parse_jobs 中 status != 'failed' 的筆數。

F47：YouTube 資源消耗 2 份配額（YOUTUBE_QUOTA_COST）：
  - reserve_youtube_quota(db, user, resource_id)：
      先預檢剩餘 >= 2，再插入 2 個 stub QUEUED ParseJob（計量用）
  - refund_quota(db, resource_id)：
      把上述 stub job 標記 FAILED，退回 2 份計量
"""

from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.plan_quota import PlanQuota
from app.models.resource import Resource
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
from app.models.user import User


UNLIMITED = -1

# YouTube 上傳消耗 2 份配額
YOUTUBE_QUOTA_COST = 2

# ParseJob metadata tag 用來識別是「配額佔位 stub」
_YT_QUOTA_STUB_TAG = "yt_quota_stub"


class QuotaExceededError(Exception):
    """配額用盡；API 層捕獲後回 402."""

    def __init__(self, limit: int, used: int, plan: str):
        """初始化實例。"""
        self.limit = limit
        self.used = used
        self.plan = plan
        super().__init__(
            f"本月解析配額已用完（方案 {plan}：{used}/{limit}）"
        )


def _month_start_utc(now: datetime | None = None) -> datetime:
    """ month start utc。"""
    now = now or datetime.now(timezone.utc)
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_quota_limit(db: Session, plan: str) -> int | None:
    """回傳該方案月配額；None 代表未設定（視為拒絕）。"""
    return db.execute(
        select(PlanQuota.monthly_resource_parse_limit).where(PlanQuota.plan == plan)
    ).scalar_one_or_none()


def get_usage_this_month(db: Session, user_id: UUID) -> int:
    """取得 usage this month。"""
    since = _month_start_utc()
    return db.execute(
        select(func.count(ResourceParseJob.id))
        .join(Resource, ResourceParseJob.resource_id == Resource.id)
        .where(
            and_(
                Resource.user_id == user_id,
                ResourceParseJob.created_at >= since,
                ResourceParseJob.status != ParseJobStatus.FAILED.value,
            )
        )
    ).scalar_one()


def check_and_consume(db: Session, user: User, cost: int = 1) -> None:
    """發起解析前呼叫。若超額拋 QuotaExceededError。

    cost：本次消耗的配額份數（普通資源=1，YouTube=2）。
    解析 job 的 row 本身就是計量單位；此函式只做檢查，不扣配額。
    """
    raw_plan = getattr(user, "subscription_plan", None)
    # subscription_plan 可能是 SubscriptionPlan enum；DB 存字串。
    # 解 enum.value，否則 SQL filter 會 mismatch（產生 limit=0 假錯）。
    plan = getattr(raw_plan, "value", raw_plan) or "FREE"
    limit = get_quota_limit(db, plan)

    if limit == UNLIMITED:
        return
    if limit is None or limit <= 0:
        raise QuotaExceededError(limit=limit or 0, used=0, plan=plan)

    used = get_usage_this_month(db, user.id)
    # 剩餘配額必須 >= cost 才可繼續
    if used + cost > limit:
        raise QuotaExceededError(limit=limit, used=used, plan=plan)


def reserve_youtube_quota(
    db: Session,
    user: User,
    resource_id: UUID | str | None = None,
    tenant_id: UUID | str | None = None,
    skip_check: bool = False,
) -> None:
    """YouTube 上傳前：預檢 2 份配額，並插入 2 個 stub QUEUED ParseJob 佔位計量。

    Args:
        db: 資料庫 session
        user: 上傳者
        resource_id: 已建立的 Resource.id（若提供則寫入 stub job；None 時只做預檢）
        tenant_id: 多租戶鍵
        skip_check: True 表示跳過配額預檢（已在外層完成），只插入 stub rows

    Raises:
        QuotaExceededError: 剩餘配額 < 2（skip_check=False 時）
    """
    # 1. 預檢：剩餘 >= 2（可跳過以避免雙重計算）
    if not skip_check:
        check_and_consume(db, user, cost=YOUTUBE_QUOTA_COST)

    # 2. 若提供 resource_id，插入 2 個計量 stub（QUEUED 狀態，即計入用量）
    if resource_id is not None:
        rid = _uuid.UUID(str(resource_id))
        tid = _uuid.UUID(str(tenant_id)) if tenant_id else None
        for _ in range(YOUTUBE_QUOTA_COST):
            stub = ResourceParseJob(
                resource_id=rid,
                tenant_id=tid,
                status=ParseJobStatus.QUEUED.value,
                gemini_model=_YT_QUOTA_STUB_TAG,
            )
            db.add(stub)
        db.commit()


def refund_quota(
    db: Session,
    user_id: UUID | str,
    resource_id: UUID | str,
) -> None:
    """退回指定 resource 的 YouTube 配額（把 stub jobs 標記 FAILED）。

    用於 YouTube 上傳背景排程失敗時退回 2 份配額。
    計量邏輯：get_usage_this_month 排除 FAILED jobs，
    因此把 stub jobs 標記 FAILED 即自動退回配額。
    """
    if isinstance(resource_id, str):
        resource_id = _uuid.UUID(resource_id)

    try:
        jobs = db.execute(
            select(ResourceParseJob).where(
                and_(
                    ResourceParseJob.resource_id == resource_id,
                    ResourceParseJob.gemini_model == _YT_QUOTA_STUB_TAG,
                )
            )
        ).scalars().all()

        for job in jobs:
            job.status = ParseJobStatus.FAILED.value
            job.failure_reason = "yt_quota_refund: enqueue failed"

        db.commit()
    except Exception:
        db.rollback()
        raise
