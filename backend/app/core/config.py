"""路徑管理與設定模組 - E2E Testing."""

import os
from pathlib import Path
from functools import lru_cache

# Load .env file (only if it exists, does NOT override system env vars)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)


class Paths:
    """專案路徑管理。"""

    def __init__(self):
        # 專案根目錄
        self.ROOT = Path(__file__).parent.parent.parent.resolve()

        # 主要目錄
        self.APP = self.ROOT / "app"
        self.TESTS = self.ROOT / "tests"
        self.SPECS = self.ROOT / "project/specs"
        self.ALEMBIC = self.ROOT / "alembic"

        # 子目錄
        self.MODELS = self.APP / "models"
        self.REPOSITORIES = self.APP / "repositories"
        self.SERVICES = self.APP / "services"
        self.API = self.APP / "api"
        self.CORE = self.APP / "core"

        # 測試目錄
        self.FEATURES = self.TESTS / "features"
        self.E2E_FEATURES = self.TESTS / "features"

        # 配置檔案
        self.ALEMBIC_INI = self.ROOT / "alembic.ini"
        self.DBML = self.SPECS / "erm.dbml"


class Settings:
    """應用程式設定。"""

    def __init__(self):
        # 資料庫設定
        self.DATABASE_URL: str = os.environ.get(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/certimate-api_dev"
        )

        # JWT 設定
        self.JWT_SECRET_KEY: str = os.environ.get(
            "JWT_SECRET_KEY",
            "certimate-api-test-secret-key-do-not-use-in-production"
        )
        self.JWT_ALGORITHM: str = "HS256"  # 安全限制：僅允許 HS256/RS256/ES256
        assert self.JWT_ALGORITHM in ("HS256", "RS256", "ES256"), \
            f"Unsafe JWT algorithm: {self.JWT_ALGORITHM}"
        # JWT TTL：8 小時涵蓋長時間測驗（最長模擬考 4-5 小時 + 考後分析）
        # 可由環境變數覆寫；若 < 4 視為設定錯誤強制改 4
        _ttl = int(os.environ.get("JWT_EXPIRE_HOURS", "8"))
        self.JWT_EXPIRE_HOURS: int = max(_ttl, 4)

        # API 設定
        self.API_V1_PREFIX: str = "/api/v1"
        self.PROJECT_NAME: str = "CertiMate API"
        self.DEBUG: bool = os.environ.get("DEBUG", "true").lower() == "true"

        # CORS — comma-separated origins, empty = allow all
        self.ALLOWED_ORIGINS: str = os.environ.get("ALLOWED_ORIGINS", "")

        # Frontend URL (for email verification links)
        self.FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "http://localhost:3000")

        # SMTP email settings (Gmail: smtp.gmail.com, port 587, App Password)
        self.SMTP_HOST: str = os.environ.get("SMTP_HOST", "")
        self.SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
        self.SMTP_USER: str = os.environ.get("SMTP_USER", "")
        self.SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
        self.SMTP_FROM_EMAIL: str = os.environ.get("SMTP_FROM_EMAIL", "noreply@certimate.app")

        # Google OAuth (for verifying Google Sign-In ID tokens)
        self.GOOGLE_CLIENT_ID: str = os.environ.get("GOOGLE_CLIENT_ID", "")
        # Firebase project ID (for verifying Firebase ID tokens, aud claim)
        self.FIREBASE_PROJECT_ID: str = os.environ.get("FIREBASE_PROJECT_ID", "certimate-titi")

        # AI / RAG 設定 — API Keys
        self.ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
        self.OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
        self.GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
        self.VOYAGE_API_KEY: str = os.environ.get("VOYAGE_API_KEY", "")

        # AI / RAG 設定 — 預設模型（可被 ai_model_routings 表覆蓋）
        self.CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")
        self.CLAUDE_PDF_MODEL: str = os.environ.get("CLAUDE_PDF_MODEL", "claude-sonnet-4-5")
        self.CLAUDE_HAIKU_MODEL: str = os.environ.get("CLAUDE_HAIKU_MODEL", "claude-haiku-4-5")
        self.OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.VOYAGE_EMBED_MODEL: str = os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3")

        # RAG 參數
        self.CHUNK_SIZE_TOKENS: int = int(os.environ.get("CHUNK_SIZE_TOKENS", "512"))
        self.CHUNK_OVERLAP_TOKENS: int = int(os.environ.get("CHUNK_OVERLAP_TOKENS", "64"))
        self.RETRIEVAL_TOP_K: int = int(os.environ.get("RETRIEVAL_TOP_K", "10"))
        self.EMBEDDING_DIMENSIONS: int = int(os.environ.get("EMBEDDING_DIMENSIONS", "1024"))

        # GCP Billing Export 設定（Feature 33）
        self.GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
        self.GCP_BILLING_EXPORT_DATASET: str = os.environ.get(
            "GCP_BILLING_EXPORT_DATASET", "billing_export"
        )
        self.GCP_BILLING_EXPORT_TABLE: str = os.environ.get(
            "GCP_BILLING_EXPORT_TABLE", "gcp_billing_export_v1"
        )
        self.GCP_BQ_CREDENTIALS_PATH: str = os.environ.get("GCP_BQ_CREDENTIALS_PATH", "")
        self.GCP_BILLING_MODE: str = os.environ.get("GCP_BILLING_MODE", "fake")  # fake | real

        # GCP Native Budget API 設定
        self.GCP_BUDGET_PARENT: str = os.environ.get("GCP_BUDGET_PARENT", "")

        # 成本監控預警通知設定
        self.COST_ALERT_EMAILS: str = os.environ.get("COST_ALERT_EMAILS", "")  # comma-separated


# 單例實例
paths = Paths()

# 預設 B2C 租戶 UUID（所有模組共用此常數，不要在其他地方重複定義）
PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"


@lru_cache()
def get_settings() -> Settings:
    """取得設定單例。"""
    return Settings()
