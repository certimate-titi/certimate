"""週報寄送 Service — 生成並寄送學習週報。"""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.models.exam import Exam, ExamStatus
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
    """Weekly Report Service 服務類別。"""
    def __init__(self, db: Session):
        """初始化實例。"""
        self.db = db
        self.email_service = EmailService()
        self._llm = None
        self._prompt_svc = None

    def _get_llm(self):
        """取得 llm。"""
        if self._llm is None:
            from app.core.config import get_settings
            settings = get_settings()
            if settings.GEMINI_API_KEY or settings.ANTHROPIC_API_KEY or settings.OPENAI_API_KEY:
                from app.services.llm_service import LLMService
                self._llm = LLMService(db=self.db)
        return self._llm

    def _load_prompt(self, name: str, variables: dict | None = None) -> dict | None:
        """載入 prompt。"""
        if not self._prompt_svc:
            try:
                from app.services.prompt_template_service import PromptTemplateService
                self._prompt_svc = PromptTemplateService(self.db)
            except Exception:
                return None
        try:
            result = self._prompt_svc.get_prompt_for_ai(name)
            if result.get("error"):
                return None
            if variables:
                render = self._prompt_svc.render_prompt
                result["system_prompt"] = render(result["system_prompt"], variables)
                result["user_prompt"] = render(result["user_prompt"], variables)
            return result
        except Exception:
            return None

    def _generate_ai_summary(self, user: User, week_start: datetime, week_end: datetime) -> str | None:
        """收集用戶本週學習數據並透過 LLM 生成 AI 週報摘要。

        Returns:
            markdown 格式摘要文字，或 None（LLM 不可用時）
        """
        llm = self._get_llm()
        if not llm:
            return None

        # 收集本週學習數據
        exams = (
            self.db.query(Exam)
            .filter(
                Exam.user_id == user.id,
                Exam.status == ExamStatus.SUBMITTED,
                Exam.submitted_at >= week_start,
                Exam.submitted_at <= week_end,
            )
            .all()
        )

        total_questions = sum(e.total_questions or 0 for e in exams)
        total_correct = sum(e.correct_count or 0 for e in exams)
        accuracy = round(total_correct / total_questions * 100) if total_questions > 0 else 0

        weekly_stats = {
            "total_questions": total_questions,
            "accuracy": accuracy,
            "exams_taken": len(exams),
            "streak_days": getattr(user, 'streak_days', 0) or 0,
            "study_minutes": 0,  # TODO: integrate pomodoro data
        }

        stats_json = json.dumps(weekly_stats, ensure_ascii=False)
        display_name = user.display_name or user.email.split("@")[0]
        week_str = f"{week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')}"

        db_prompt = self._load_prompt("weekly_report", {
            "display_name": display_name,
            "week_range": week_str,
            "weekly_stats": stats_json,
        })

        if db_prompt:
            system_prompt = db_prompt["system_prompt"]
            user_prompt = db_prompt["user_prompt"]
        else:
            system_prompt = (
                "你是 TiTi 學習教練 Certi。根據以下學習數據，生成一段溫暖的週報摘要。"
                "語調溫暖正向，絕不使用負面詞彙。包含：本週亮點、具體數據回顧、下週建議。"
                "使用 markdown 格式，長度 150-250 字。"
            )
            user_prompt = (
                f"學生：{display_name}\n"
                f"週期：{week_str}\n"
                f"學習數據：\n{stats_json}"
            )

        try:
            result = llm.generate(
                system_prompt, user_prompt,
                model="gemini-flash", max_tokens=512,
            )
            if result and len(result.strip()) > 10:
                return result.strip()
        except Exception as e:
            logger.warning("F-02 weekly_report AI summary generation failed: %s", e)

        return None

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

        # 嘗試生成 AI 摘要
        ai_summary = self._generate_ai_summary(user, week_start, week_end)

        if ai_summary:
            # 將 markdown 換行轉為 HTML
            summary_html = ai_summary.replace("\n", "<br>")
            content_section = f"""
            <div style="background:#f0fdf4;border-left:4px solid #059669;padding:16px;margin:16px 0;border-radius:4px">
                <h3 style="color:#059669;margin-top:0">AI 學習教練摘要</h3>
                <div style="color:#374151;line-height:1.6">{summary_html}</div>
            </div>"""
        else:
            content_section = """
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
            <p>繼續保持你的學習節奏，每天一點點的進步都會累積成大成就！</p>"""

        html = f"""
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:32px">
            <h2 style="color:#2563eb">CertiMate 學習週報</h2>
            <p>嗨 {display_name}，</p>
            <p>這是您 {week_str} 的學習週報。持續學習的你真的很棒！</p>
            {content_section}

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
