"""Behave 環境設定 - E2E Testing.

支援兩種模式：
1. Docker 可用時：Testcontainers + PostgreSQL（完整 E2E）
2. Docker 不可用時：SQLite in-memory（開發/CI fallback）

生命週期：
- before_all: 初始化資料庫引擎（Docker 或 SQLite）
- before_scenario: 初始化 context 狀態、DB Session、HTTP Client
- after_scenario: 清理資料（Phase 4：確保測試資料不污染正式環境）
- after_all: 關閉資源

Phase 4 BDD 測試環境隔離強化：
- 每個 Scenario 使用獨立的測試租戶 ID（is_test=True 隔離標籤）
- TRUNCATE 後重新 Seed 基礎資料（plan_quotas、public_b2c 租戶）
- 防止測試產生的向量資料、成績資料污染 RLS policy
"""

import os
import sys
from types import SimpleNamespace

# 確保專案根目錄在 Python path 中
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 全域變數（session scope）
_postgres_container = None
_engine = None
_SessionLocal = None
_using_sqlite = False


def _try_start_postgres():
    """嘗試使用 Testcontainers 啟動 PostgreSQL。"""
    global _postgres_container, _engine, _SessionLocal

    from testcontainers.postgres import PostgresContainer
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    _postgres_container = PostgresContainer(
        image="pgvector/pgvector:pg15",
        username="postgres",
        password="postgres",
        dbname="certimate-api_test"
    )
    _postgres_container.start()

    connection_url = _postgres_container.get_connection_url()
    connection_url = connection_url.replace("psycopg2", "psycopg")

    os.environ["DATABASE_URL"] = connection_url
    _engine = create_engine(connection_url)

    # 執行 Alembic migrations
    from alembic.config import Config
    from alembic import command
    from app.core.config import paths

    alembic_cfg = Config(str(paths.ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", connection_url)
    command.upgrade(alembic_cfg, "head")

    _SessionLocal = sessionmaker(bind=_engine)


def _start_sqlite():
    """使用 SQLite in-memory 作為 fallback。"""
    global _engine, _SessionLocal, _using_sqlite

    from sqlalchemy import String, create_engine, event
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    import sqlite3
    import uuid as _uuid

    _using_sqlite = True

    # 註冊 UUID 類型適配器讓 SQLite 能處理 Python uuid 物件
    sqlite3.register_adapter(_uuid.UUID, lambda u: str(u))
    sqlite3.register_converter("UUID", lambda b: _uuid.UUID(b.decode()))

    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"detect_types": sqlite3.PARSE_DECLTYPES, "check_same_thread": False},
        pool_pre_ping=True,
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
    )

    @event.listens_for(_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # SQLite: 將 PostgreSQL 專用型別替換為可攜帶型別
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    from sqlalchemy import Enum as SA_Enum

    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, PG_UUID):
                column.type = String(36)
            elif isinstance(column.type, SA_Enum):
                column.type = String(50)

    Base.metadata.create_all(bind=_engine)
    _SessionLocal = sessionmaker(bind=_engine)


def before_all(context):
    """初始化資料庫（優先 Docker，fallback SQLite）。"""
    global _postgres_container, _engine, _SessionLocal

    try:
        _try_start_postgres()
        print("✓ 使用 Testcontainers + PostgreSQL")
    except Exception as e:
        print(f"⚠ Docker 不可用 ({type(e).__name__}), 使用 SQLite fallback")
        _start_sqlite()

    # 設定依賴注入
    from app.core.deps import set_session_factory
    set_session_factory(_SessionLocal)


# Phase 4: 測試專用租戶 UUID（固定值，與 migration 038 public_b2c 不同）
TEST_TENANT_ID = "ffffffff-0000-0000-0000-000000000001"
PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"


def _seed_base_data(session):
    """Seed 所有 Scenario 都需要的基礎資料（plan_quotas + 預設租戶）。

    Phase 4 強化：TRUNCATE 後重新植入，確保測試環境乾淨。
    """
    from sqlalchemy import text

    # 1. Seed plan_quotas
    from app.models.plan_quota import PlanQuota

    defaults = [
        {"plan": "FREE", "daily_ai_chats": 3, "monthly_uploads": 5, "monthly_exams": 10, "monthly_vision_pages": 0, "max_file_size_mb": 10},
        {"plan": "PRO_199", "daily_ai_chats": 30, "monthly_uploads": 50, "monthly_exams": 100, "monthly_vision_pages": 0, "max_file_size_mb": 100},
        {"plan": "PRO_PLUS_399", "daily_ai_chats": 200, "monthly_uploads": 200, "monthly_exams": 500, "monthly_vision_pages": 50, "max_file_size_mb": 100},
        {"plan": "ULTRA_1599", "daily_ai_chats": None, "monthly_uploads": None, "monthly_exams": None, "monthly_vision_pages": 500, "max_file_size_mb": 500},
        {"plan": "EDU", "daily_ai_chats": 5, "monthly_uploads": 0, "monthly_exams": None, "monthly_vision_pages": 0, "max_file_size_mb": 0},
    ]
    for row in defaults:
        existing = session.query(PlanQuota).filter_by(plan=row["plan"]).first()
        if existing is None:
            session.add(PlanQuota(**row))

    # 2. Seed 預設 B2C 租戶（若 tenants 表存在）
    try:
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(session.get_bind())
        if "tenants" in inspector.get_table_names():
            session.execute(
                text(
                    "INSERT INTO tenants (id, slug, name, plan_tier, is_active) "
                    "VALUES (:id, 'public_b2c', '公開 B2C 平台', 'b2c', true) "
                    "ON CONFLICT (slug) DO NOTHING"
                ),
                {"id": PUBLIC_B2C_TENANT_ID},
            )
            # 同時植入測試專用租戶（is_test 隔離）
            session.execute(
                text(
                    "INSERT INTO tenants (id, slug, name, plan_tier, is_active) "
                    "VALUES (:id, 'test_tenant', '測試租戶（BDD）', 'b2c', true) "
                    "ON CONFLICT (slug) DO NOTHING"
                ),
                {"id": TEST_TENANT_ID},
            )
    except Exception:
        pass  # tenants 表可能尚未建立（migration < 038）

    session.commit()


# 向後相容別名
def _seed_plan_quotas(session):
    """向後相容：等同於 _seed_base_data。"""
    _seed_base_data(session)


def before_scenario(context, scenario):
    """每個 Scenario 執行前初始化。"""
    context.last_error = None
    context.last_response = None
    context.query_result = None
    context.ids = {}
    context.memo = {}

    # Phase 4: 標記測試 context，防止測試資料誤寫入正式租戶
    context.is_test = True
    context.test_tenant_id = TEST_TENANT_ID
    context.public_b2c_tenant_id = PUBLIC_B2C_TENANT_ID

    # 初始化 DB Session
    context.db_session = _SessionLocal()

    # Seed 基礎資料（plan_quotas + 預設租戶）
    _seed_base_data(context.db_session)

    # 初始化 HTTP Client（FastAPI TestClient）
    from fastapi.testclient import TestClient
    from app.main import app
    context.api_client = TestClient(app)

    # 初始化 JWT Helper
    from tests.features.helpers.jwt_helper import JwtHelper
    context.jwt_helper = JwtHelper()

    # 初始化 Repositories / Services namespace
    context.repos = SimpleNamespace()
    context.services = SimpleNamespace()


def after_scenario(context, scenario):
    """每個 Scenario 執行後清理。"""
    # Rollback 任何未提交的變更
    context.db_session.rollback()

    if _using_sqlite:
        # SQLite: 刪除所有資料
        from app.models import Base
        for table in reversed(Base.metadata.sorted_tables):
            context.db_session.execute(table.delete())
        context.db_session.commit()
    else:
        # PostgreSQL: Truncate all tables
        from sqlalchemy import inspect, text
        inspector = inspect(_engine)
        tables = inspector.get_table_names()
        with _engine.begin() as connection:
            for table in tables:
                if table != 'alembic_version':
                    connection.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

    context.db_session.close()

    # 重設 ecpay_service 的時間函數
    try:
        from app.services.ecpay_service import set_now_func
        set_now_func(None)
    except ImportError:
        pass

    # 重設 GcpBillingService 的測試 hook（Feature 33）
    try:
        from app.services.gcp_billing_service import set_test_override, set_test_services, set_test_daily_series
        set_test_override(None)
        set_test_services(None)
        set_test_daily_series(None)
    except ImportError:
        pass

    # Feature 33: 重設 GCP billing test override + GCP budget sync factory
    try:
        from app.services.gcp_billing_service import set_test_override
        set_test_override(None)
    except ImportError:
        pass
    try:
        import app.services.gcp_budget_sync_service as _gbs
        if hasattr(_gbs, "_original_make_default_adapter"):
            _gbs._make_default_adapter = _gbs._original_make_default_adapter
        else:
            # Cache the pristine factory the first time we see it
            _gbs._original_make_default_adapter = _gbs._make_default_adapter
    except ImportError:
        pass

    # 清理狀態
    context.last_error = None
    context.last_response = None
    context.query_result = None
    context.ids.clear()
    context.memo.clear()


def after_all(context):
    """關閉資源。"""
    global _postgres_container, _engine

    if _engine:
        _engine.dispose()
    if _postgres_container:
        _postgres_container.stop()
