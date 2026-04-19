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

    # 4) Feature 33 — 預算告警評估（每 30 分鐘）
    import os
    if os.environ.get("BUDGET_ALERT_SCHEDULER_ENABLED", "true").lower() == "true":
        interval_min = int(os.environ.get("BUDGET_ALERT_INTERVAL_MINUTES", "30"))
        from apscheduler.triggers.interval import IntervalTrigger
        _scheduler.add_job(
            job_budget_alert_evaluate,
            IntervalTrigger(minutes=interval_min),
            id="budget_alert_evaluate",
            name=f"Feature 33 預算告警評估（每 {interval_min} 分鐘）",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )

    # 5) 審計日誌清理 — 每天 03:00 刪除 90 天以前的紀錄
    retention_days = int(os.environ.get("AUDIT_LOG_RETENTION_DAYS", "90"))
    _scheduler.add_job(
        job_audit_log_cleanup,
        CronTrigger(hour=3, minute=0),
        id="audit_log_cleanup",
        name=f"審計日誌清理（保留 {retention_days} 天）",
        replace_existing=True,
    )

    # 6) ai_usage_ledger 清理 — 每月 1 號 04:00 刪除 12 個月以前的紀錄
    _scheduler.add_job(
        job_usage_ledger_cleanup,
        CronTrigger(day=1, hour=4, minute=0),
        id="usage_ledger_cleanup",
        name="AI 用量帳本清理（保留 12 個月）",
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


async def job_budget_alert_evaluate():
    """Feature 33 TODO #6 — 定期評估所有 scope 的預算門檻，
    寫入 budget_alert_log 並觸發通知管道。"""
    db = _get_db()
    try:
        from app.services.budget_service import BudgetService
        result = BudgetService(db).evaluate_alerts()
        fired = result.get("fired", []) if isinstance(result, dict) else []
        if fired:
            logger.warning(
                "Budget alert evaluate fired %d alerts: %s",
                len(fired),
                [f.get("scope") for f in fired],
            )
        else:
            logger.debug("Budget alert evaluate: no alerts fired")
    except Exception:
        db.rollback()
        logger.exception("Budget alert evaluate job failed")
    finally:
        db.close()


async def job_audit_log_cleanup():
    """刪除超過 retention_days 天的審計日誌。

    保留近期紀錄供合規查詢，刪除老舊紀錄避免 DB 膨脹。
    每天 03:00 執行，AUDIT_LOG_RETENTION_DAYS 環境變數可調（預設 90 天）。
    """
    import os
    from sqlalchemy import text
    db = _get_db()
    try:
        days = int(os.environ.get("AUDIT_LOG_RETENTION_DAYS", "90"))
        result = db.execute(
            text("DELETE FROM admin_audit_logs WHERE created_at < NOW() - INTERVAL :days"),
            {"days": f"{days} days"},
        )
        deleted = result.rowcount
        db.commit()
        if deleted > 0:
            logger.info("Audit log cleanup: deleted %d rows older than %d days", deleted, days)
    except Exception:
        db.rollback()
        logger.exception("Audit log cleanup failed")
    finally:
        db.close()


async def job_usage_ledger_cleanup():
    """刪除超過 12 個月的 AI 用量帳本紀錄。

    ai_usage_ledger 用於 cost monitor 月報表；超過 12 個月的不需要逐筆保留。
    每月 1 號 04:00 執行。
    """
    from sqlalchemy import text
    db = _get_db()
    try:
        result = db.execute(
            text("DELETE FROM ai_usage_ledger WHERE created_at < NOW() - INTERVAL '12 months'"),
        )
        deleted = result.rowcount
        db.commit()
        if deleted > 0:
            logger.info("Usage ledger cleanup: deleted %d rows older than 12 months", deleted)
    except Exception:
        db.rollback()
        logger.exception("Usage ledger cleanup failed")
    finally:
        db.close()
