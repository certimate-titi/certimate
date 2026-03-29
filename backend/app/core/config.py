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
        self.JWT_ALGORITHM: str = "HS256"
        self.JWT_EXPIRE_HOURS: int = 1

        # API 設定
        self.API_V1_PREFIX: str = "/api/v1"
        self.PROJECT_NAME: str = "CertiMate API"
        self.DEBUG: bool = os.environ.get("DEBUG", "true").lower() == "true"

        # AI / RAG 設定 — API Keys
        self.ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
        self.OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
        self.GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
        self.VOYAGE_API_KEY: str = os.environ.get("VOYAGE_API_KEY", "")

        # AI / RAG 設定 — 預設模型（可被 ai_model_routings 表覆蓋）
        self.CLAUDE_MODEL: str = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self.CLAUDE_PDF_MODEL: str = os.environ.get("CLAUDE_PDF_MODEL", "claude-sonnet-4-20250514")
        self.OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o")
        self.GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.VOYAGE_EMBED_MODEL: str = os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3")

        # RAG 參數
        self.CHUNK_SIZE_TOKENS: int = int(os.environ.get("CHUNK_SIZE_TOKENS", "512"))
        self.CHUNK_OVERLAP_TOKENS: int = int(os.environ.get("CHUNK_OVERLAP_TOKENS", "64"))
        self.RETRIEVAL_TOP_K: int = int(os.environ.get("RETRIEVAL_TOP_K", "10"))
        self.EMBEDDING_DIMENSIONS: int = int(os.environ.get("EMBEDDING_DIMENSIONS", "1024"))


# 單例實例
paths = Paths()


@lru_cache()
def get_settings() -> Settings:
    """取得設定單例。"""
    return Settings()
