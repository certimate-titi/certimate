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

        try:
            with smtplib.SMTP(host, self.settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
                server.sendmail(self.settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            logger.info("Email sent to %s: %s", to_email, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to_email)
            return False

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
