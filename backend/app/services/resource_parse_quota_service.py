"""Resource parse quota service — EPIC-035 M6 TASK-06.

檢查用戶本月可用 LLM 解析配額：
  FREE=5 / PRO=50 / PRO_PLUS=200 / ULTRA=-1（無限）

配額以日曆月計算（每月 1 日 00:00 UTC 重置）。
計量單位：該用戶當月 resource_parse_jobs 中 status != 'failed' 的筆數。
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.plan_quota import PlanQuota
from app.models.resource import Resource
from app.models.resource_parse_job import ParseJobStatus, ResourceParseJob
from app.models.user import User


UNLIMITED = -1


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


def check_and_consume(db: Session, user: User) -> None:
    """發起解析前呼叫。若超額拋 QuotaExceededError。

    解析 job 的 row 本身就是計量單位；此函式只做檢查，不扣配額。
    """
    plan = getattr(user, "subscription_plan", None) or "FREE"
    limit = get_quota_limit(db, plan)

    if limit == UNLIMITED:
        return
    if limit is None or limit <= 0:
        raise QuotaExceededError(limit=limit or 0, used=0, plan=plan)

    used = get_usage_this_month(db, user.id)
    if used >= limit:
        raise QuotaExceededError(limit=limit, used=used, plan=plan)
