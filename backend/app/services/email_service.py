"""Email service — sends transactional emails via SMTP."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:

    def __init__(self):
        self.settings = get_settings()

    def _send(self, to_email: str, subject: str, html_body: str) -> bool:
        host = self.settings.SMTP_HOST
        if not host:
            logger.warning("SMTP not configured — skipping email to %s", to_email)
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = f"CertiMate <{self.settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        port = self.settings.SMTP_PORT
        try:
            if port == 465:
                # SSL (port 465) — used when STARTTLS on 587 is blocked (e.g. Cloud Run)
                with smtplib.SMTP_SSL(host, port, timeout=15) as server:
                    server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                    server.sendmail(self.settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            else:
                # STARTTLS (port 587) — standard
                with smtplib.SMTP(host, port, timeout=15) as server:
                    server.starttls()
                    server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                    server.sendmail(self.settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            logger.info("Email sent to %s: %s (port %d)", to_email, subject, port)
            return True
        except Exception:
            logger.exception("Failed to send email to %s (port %d)", to_email, port)
            return False

    def send_budget_alert(
        self,
        to_email: str,
        *,
        scope: str,
        alert_type: str,
        current_usd: float,
        limit_usd: float,
        percent: float,
    ) -> bool:
        """Send a Feature 33 budget alert email to a Super Admin.

        TODO #5 — Replaces the previous stub where evaluate_alerts only
        wrote to budget_alert_log without actually notifying anyone.
        """
        tier_label = {
            "WARNING": "⚠️ 警告",
            "DEGRADE": "🟠 降級",
            "DISABLED": "🔴 停用",
        }.get(alert_type, alert_type)

        subject = f"[CertiMate] {tier_label} {scope} 預算達 {percent:.1f}%"
        html = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px">
            <h2 style="color:#dc2626">CertiMate 預算告警 — {tier_label}</h2>
            <p style="font-size:16px;line-height:1.6">
                <b>{scope}</b> 當月用量已達 <b>{percent:.1f}%</b>，自動觸發 <b>{alert_type}</b> 狀態。
            </p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0">
                <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb">當月已花費</td>
                    <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:bold">
                        ${current_usd:.2f}</td></tr>
                <tr><td style="padding:8px;border-bottom:1px solid #e5e7eb">月預算上限</td>
                    <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:right">
                        ${limit_usd:.2f}</td></tr>
                <tr><td style="padding:8px">使用率</td>
                    <td style="padding:8px;text-align:right;color:#dc2626;font-weight:bold">
                        {percent:.1f}%</td></tr>
            </table>
            <p style="margin-top:24px">
                <a href="{self.settings.FRONTEND_URL}/super-admin/cost-monitor"
                   style="display:inline-block;padding:10px 24px;background:#10b981;color:#fff;
                          text-decoration:none;border-radius:8px;font-weight:bold">
                    前往成本監控中心
                </a>
            </p>
            <p style="color:#6b7280;font-size:12px;margin-top:32px">
                此為自動化告警，由 CertiMate Feature 33 成本監控中心發送。
                若您不是 Super Admin 請忽略此信。
            </p>
        </div>
        """
        return self._send(to_email, subject, html)

    def send_password_reset_email(self, to_email: str, token: str) -> bool:
        url = f"{self.settings.FRONTEND_URL}/reset-password?token={token}"
        html = f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
            <h2 style="color:#10b981">CertiMate — 重設密碼</h2>
            <p style="font-size:15px;line-height:1.6;color:#334155">
                您收到這封信是因為有人對您的帳號提出了密碼重設請求。<br>
                點擊下方按鈕來設定新密碼：
            </p>
            <a href="{url}"
               style="display:inline-block;padding:12px 32px;background:#10b981;color:#fff;
                      text-decoration:none;border-radius:8px;font-weight:bold;margin:16px 0">
                重設我的密碼
            </a>
            <p style="color:#6b7280;font-size:14px">
                此連結將於 1 小時後失效。<br>
                若您未提出此請求，請忽略此信，您的密碼不會被更改。
            </p>
            <p style="color:#94a3b8;font-size:12px;margin-top:24px">
                如果您是使用 Google 登入的用戶，設定密碼後可同時使用 Email 和 Google 兩種方式登入。
            </p>
        </div>
        """
        return self._send(to_email, "[CertiMate] 重設您的密碼", html)

    def send_verification_email(self, to_email: str, token: str) -> bool:
        url = f"{self.settings.FRONTEND_URL}/verify-email?token={token}"
        html = f"""
        <div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px">
            <h2 style="color:#2563eb">CertiMate — Email 驗證</h2>
            <p>感謝您註冊 CertiMate！請點擊下方按鈕完成帳號驗證：</p>
            <a href="{url}"
               style="display:inline-block;padding:12px 32px;background:#2563eb;color:#fff;
                      text-decoration:none;border-radius:8px;font-weight:bold;margin:16px 0">
                驗證我的帳號
            </a>
            <p style="color:#6b7280;font-size:14px">
                此連結將於 24 小時後失效。<br>
                若您未申請此帳號，請忽略此信。
            </p>
        </div>
        """
        return self._send(to_email, "CertiMate — 請驗證您的帳號", html)
