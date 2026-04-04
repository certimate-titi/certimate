"""週報寄送 Service — 生成並寄送學習週報。"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.services.email_service import EmailService

logger = logging.getLogger("certimate.weekly_report")

# 方案有週報功能：PRO, PRO_PLUS, ULTRA, EDU
WEEKLY_REPORT_PLANS = {
    SubscriptionPlan.PRO,
    SubscriptionPlan.PRO_PLUS,
    SubscriptionPlan.ULTRA,
    SubscriptionPlan.EDU,
}


class WeeklyReportService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    def get_active_users_for_report(self) -> list[User]:
        """取得過去 7 天有登入且方案含週報功能的活躍用戶。"""
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        users = (
            self.db.query(User)
            .filter(
                User.subscription_plan.in_(WEEKLY_REPORT_PLANS),
                User.subscription_status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL,
                ]),
                User.last_login_at >= seven_days_ago,
            )
            .all()
        )

        return users

    def generate_report_html(self, user: User, week_start: datetime, week_end: datetime) -> str:
        """為單一用戶生成週報 HTML。"""
        display_name = user.display_name or user.email.split("@")[0]
        week_str = f"{week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')}"

        # TODO: 整合真實學習統計數據（T16 之後）
        html = f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:32px">
            <h2 style="color:#2563eb">CertiMate 學習週報</h2>
            <p>嗨 {display_name}，</p>
            <p>這是您 {week_str} 的學習週報。持續學習的你真的很棒！</p>

            <table style="width:100%;border-collapse:collapse;margin:16px 0">
                <tr style="background:#f1f5f9">
                    <th style="padding:8px;text-align:left;border:1px solid #e2e8f0">項目</th>
                    <th style="padding:8px;text-align:center;border:1px solid #e2e8f0">本週</th>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #e2e8f0">學習天數</td>
                    <td style="padding:8px;text-align:center;border:1px solid #e2e8f0">--</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #e2e8f0">測驗次數</td>
                    <td style="padding:8px;text-align:center;border:1px solid #e2e8f0">--</td>
                </tr>
                <tr>
                    <td style="padding:8px;border:1px solid #e2e8f0">AI 對話次數</td>
                    <td style="padding:8px;text-align:center;border:1px solid #e2e8f0">--</td>
                </tr>
            </table>

            <h3 style="color:#059669">下週建議</h3>
            <p>繼續保持你的學習節奏，每天一點點的進步都會累積成大成就！</p>

            <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0">
            <p style="color:#6b7280;font-size:12px">
                CertiMate 團隊 — 讓備考更聰明<br>
                <a href="https://certimate.app" style="color:#2563eb">certimate.app</a>
            </p>
        </div>
        """
        return html

    def send_weekly_reports(self) -> dict:
        """批次寄送週報。"""
        now = datetime.now(timezone.utc)
        week_end = now
        week_start = now - timedelta(days=7)

        users = self.get_active_users_for_report()
        sent = 0
        failed = 0

        for user in users:
            html = self.generate_report_html(user, week_start, week_end)
            subject = f"CertiMate 學習週報 — {week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')}"
            success = self.email_service._send(user.email, subject, html)
            if success:
                sent += 1
            else:
                failed += 1

        logger.info("Weekly reports: sent=%d, failed=%d, total=%d", sent, failed, len(users))
        return {"sent": sent, "failed": failed, "total": len(users)}
