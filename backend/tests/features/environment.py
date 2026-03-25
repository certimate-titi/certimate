"""Behave 環境設定 - E2E Testing.

支援兩種模式：
1. Docker 可用時：Testcontainers + PostgreSQL（完整 E2E）
2. Docker 不可用時：SQLite in-memory（開發/CI fallback）

生命週期：
- before_all: 初始化資料庫引擎（Docker 或 SQLite）
- before_scenario: 初始化 context 狀態、DB Session、HTTP Client
- after_scenario: 清理資料
- after_all: 關閉資源
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
        image="postgres:15",
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

    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from app.models import Base

    _using_sqlite = True
    _engine = create_engine("sqlite:///:memory:")

    # SQLite 不支援 PostgreSQL enum，需要忽略 enum 建立
    # 使用 Base.metadata.create_all 直接建表
    @event.listens_for(_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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


def before_scenario(context, scenario):
    """每個 Scenario 執行前初始化。"""
    context.last_error = None
    context.last_response = None
    context.query_result = None
    context.ids = {}
    context.memo = {}

    # 初始化 DB Session
    context.db_session = _SessionLocal()

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
