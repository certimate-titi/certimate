"""APScheduler 背景排程框架。

提供 cron / interval 排程能力，用於：
- 14 天試用自動降級
- FUP 每日用量統計
- 週報寄送
- 其他定時任務
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger("certimate.scheduler")

# 全域 scheduler 實例
_scheduler: AsyncIOScheduler | None = None
_session_factory: sessionmaker | None = None


def get_scheduler() -> AsyncIOScheduler:
    """取得全域 scheduler 實例。"""
    if _scheduler is None:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")
    return _scheduler


def _get_db() -> Session:
    """取得獨立的 DB session（供 job 使用，需自行關閉）。"""
    if _session_factory is None:
        raise RuntimeError("Session factory not set.")
    return _session_factory()


def init_scheduler(session_factory: sessionmaker) -> AsyncIOScheduler:
    """初始化 scheduler 並註冊所有 jobs。"""
    global _scheduler, _session_factory
    _session_factory = session_factory

    _scheduler = AsyncIOScheduler(timezone="Asia/Taipei")

    # --- 註冊排程任務 ---

    # 1) 試用到期自動降級 — 每天 00:05 執行
    _scheduler.add_job(
        job_trial_expiry,
        CronTrigger(hour=0, minute=5),
        id="trial_expiry",
        name="14天試用到期自動降級",
        replace_existing=True,
    )

    # 2) FUP 每日用量檢查 — 每天 23:50 執行
    _scheduler.add_job(
        job_fup_daily_check,
        CronTrigger(hour=23, minute=50),
        id="fup_daily_check",
        name="FUP每日用量軟上限檢查",
        replace_existing=True,
    )

    # 3) 週報寄送 — 每週一 08:00 執行
    _scheduler.add_job(
        job_weekly_report,
        CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="weekly_report",
        name="學習週報寄送",
        replace_existing=True,
    )

    logger.info("Scheduler initialized with %d jobs", len(_scheduler.get_jobs()))
    return _scheduler


async def start_scheduler():
    """啟動 scheduler。"""
    if _scheduler and not _scheduler.running:
        _scheduler.start()
        logger.info("✅ Scheduler started")


async def shutdown_scheduler():
    """關閉 scheduler。"""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("🔌 Scheduler stopped")


# ===========================
# 排程任務實作
# ===========================

async def job_trial_expiry():
    """檢查並降級所有已過期的試用帳號。"""
    db = _get_db()
    try:
        from app.models.user import User, SubscriptionStatus, SubscriptionPlan
        now = datetime.now(timezone.utc)

        expired_users = (
            db.query(User)
            .filter(
                User.subscription_status == SubscriptionStatus.TRIAL,
                User.trial_end_date <= now,
            )
            .all()
        )

        count = 0
        for user in expired_users:
            pre_plan = user.pre_trial_plan or "FREE"
            user.subscription_plan = SubscriptionPlan(pre_plan)
            user.subscription_status = SubscriptionStatus.ACTIVE if pre_plan != "FREE" else SubscriptionStatus.CANCELLED
            if pre_plan == "FREE":
                user.subscription_status = SubscriptionStatus.ACTIVE
                user.subscription_plan = SubscriptionPlan.FREE
            count += 1

        if count > 0:
            db.commit()
            logger.info("Trial expiry: downgraded %d users", count)
    except Exception:
        db.rollback()
        logger.exception("Trial expiry job failed")
    finally:
        db.close()


async def job_fup_daily_check():
    """FUP 軟上限檢查 — 統計 ULTRA 用戶當日 AI 呼叫數，超過 1000 次則標記。"""
    db = _get_db()
    try:
        from app.services.fup_service import FUPService
        service = FUPService(db)
        result = service.run_daily_check()
        logger.info("FUP daily check completed: %s", result)
    except Exception:
        db.rollback()
        logger.exception("FUP daily check job failed")
    finally:
        db.close()


async def job_weekly_report():
    """週報寄送 — 寄送學習週報給活躍用戶。"""
    db = _get_db()
    try:
        from app.services.weekly_report_service import WeeklyReportService
        service = WeeklyReportService(db)
        result = service.send_weekly_reports()
        logger.info("Weekly report job completed: %s", result)
    except Exception:
        db.rollback()
        logger.exception("Weekly report job failed")
    finally:
        db.close()
