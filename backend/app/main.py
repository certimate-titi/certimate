"""FastAPI 主應用程式入口 - CertiMate API。"""

import logging as _logging_setup
import sys as _sys

# Bug #4 修補（2026-04-29）— Cloud Run / 本地都要把 app logger 導向 stdout
# 否則 logger.info/warning 不會進 Cloud Logging（之前雲端故障無法追查的根因）
# 注意：必須在 import FastAPI 前設定，否則 uvicorn 自家 handler 會覆蓋 root logger
_logging_setup.basicConfig(
    level=_logging_setup.INFO,
    stream=_sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,  # 蓋掉預設 / 既有 handler，確保 stdout 路徑生效
)
# 提升 app.* logger 至 INFO（uvicorn 預設只到 WARNING）
_logging_setup.getLogger("app").setLevel(_logging_setup.INFO)

from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.deps import set_session_factory
from app.core.scheduler import init_scheduler, start_scheduler, shutdown_scheduler
from app.services.import_scheduler import (
    init_scheduler as init_import_scheduler,
    shutdown_scheduler as shutdown_import_scheduler,
)
from app.api import router as api_router

settings = get_settings()


def _run_migrations():
    """Run Alembic migrations on startup."""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        print("✅ Alembic migrations applied")
    except Exception as e:
        print(f"⚠️ Alembic migration warning: {e}")


def _seed_on_startup(session_local):
    """啟動時自動 seed 考古題 + 知識節點 + Prompt 模板（冪等：已存在則跳過）。"""
    import os
    import sys
    from sqlalchemy import text

    # 確保 backend/ 在 sys.path（Cloud Run cwd 可能不同）
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    try:
        session = session_local()

        # 1. 考古題匯入（若 questions 表為空）
        q_count = session.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        session.close()
        if q_count == 0:
            print("📦 偵測到考古題為空，開始自動匯入...")
            try:
                from scripts.import_historical_questions import main as import_questions
                import_questions()
                print("✅ 考古題匯入完成")
            except Exception as e:
                print(f"⚠️ 考古題匯入失敗: {e}")

        # 2. 更新 subjects.available_questions 計數
        session = session_local()
        session.execute(text("""
            UPDATE subjects s SET available_questions = COALESCE(sub.cnt, 0)
            FROM (
                SELECT e.subject_id, COUNT(q.id) as cnt
                FROM exams e JOIN questions q ON q.exam_id = e.id
                WHERE q.historical_source IS NOT NULL
                GROUP BY e.subject_id
            ) sub
            WHERE s.id = sub.subject_id AND (s.available_questions IS NULL OR s.available_questions != sub.cnt)
        """))
        session.commit()

        # 3. 知識節點 seed（若 knowledge_nodes 表為空且有考古題）
        kn_count = session.execute(text("SELECT COUNT(*) FROM knowledge_nodes")).scalar()
        session.close()
        if kn_count == 0 and q_count > 0:
            print("📦 偵測到知識節點為空，開始自動生成...")
            try:
                from scripts.seed_knowledge_nodes import main as seed_nodes
                seed_nodes()
                print("✅ 知識節點生成完成")
            except Exception as e:
                print(f"⚠️ 知識節點生成失敗: {e}")
            # 填充 source_text
            try:
                from scripts.populate_node_source_text import main as populate_text
                populate_text()
                print("✅ 知識節點 source_text 填充完成")
            except Exception as e:
                print(f"⚠️ source_text 填充失敗: {e}")

        # 4. Prompt 模板 seed（若 prompt_templates_v2 表為空）
        session = session_local()
        pt_count = session.execute(text("SELECT COUNT(*) FROM prompt_templates_v2")).scalar()
        session.close()
        if pt_count == 0:
            print("📦 偵測到 Prompt 模板為空，開始自動 seed...")
            try:
                from app.scripts.seed_prompts import run_seed
                run_seed()
                print("✅ Prompt 模板 seed 完成")
            except Exception as e:
                print(f"⚠️ Prompt 模板 seed 失敗: {e}")

        print("✅ 啟動 seed 檢查完成")

    except Exception as e:
        print(f"⚠️ 啟動 seed 警告: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期：啟動時初始化 DB session factory。"""
    # ── OpenTelemetry 初始化（必須在 DB 連線前完成）──────────────────
    try:
        from app.core.telemetry import setup_telemetry
        setup_telemetry(app)
    except Exception as e:
        print(f"⚠️ OpenTelemetry 初始化警告: {e}")

    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    set_session_factory(session_local)
    print(f"✅ Database connected: {settings.DATABASE_URL.split('@')[-1]}")
    _run_migrations()
    _seed_on_startup(session_local)

    # Bug #2 watchdog（2026-04-29）：啟動時掃 stale PROCESSING resources
    # OOM SIGKILL 情境下背景任務的 finally 不會跑，會留下永遠 stuck PROCESSING 的資源
    # 服務重啟（含 Cloud Run cold start / scale up）時掃過去 30 分鐘以上沒更新的 PROCESSING
    # 一律標記 FAILED 並寫 error_message，避免用戶看到永遠 spinner
    try:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import text as _text
        with session_local() as _ws:
            cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
            res = _ws.execute(
                _text(
                    "UPDATE resources SET status='FAILED', "
                    "error_message=COALESCE(error_message, '背景處理超時，啟動掃描自動標記失敗'), "
                    "updated_at=NOW() "
                    "WHERE status='PROCESSING' AND updated_at < :cutoff "
                    "RETURNING id"
                ),
                {"cutoff": cutoff},
            )
            stuck_ids = [str(row[0]) for row in res]
            _ws.commit()
            if stuck_ids:
                print(f"⚠️  Stale PROCESSING watchdog: {len(stuck_ids)} resources marked FAILED")
    except Exception as e:
        print(f"⚠️ Stale PROCESSING watchdog 警告: {e}")

    # 啟動背景排程
    init_scheduler(session_local)
    await start_scheduler()
    # 啟動 Import Job APScheduler（非同步考古題匯入）
    try:
        init_import_scheduler(settings.DATABASE_URL)
        print("✅ Import job scheduler initialized")
    except Exception as e:
        print(f"⚠️ Import scheduler init 警告: {e}")
    yield
    await shutdown_scheduler()
    try:
        shutdown_import_scheduler()
    except Exception as e:
        print(f"⚠️ Import scheduler shutdown 警告: {e}")
    engine.dispose()
    print("🔌 Database connection closed")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.3.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    lifespan=lifespan,
)

# CORS 設定
_allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 多租戶限流 Middleware（Token Bucket；Redis + 記憶體 Fallback）
try:
    from app.core.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"限流 Middleware 載入失敗（已跳過）: {_e}")

# LLM 防火牆例外處理（Prompt Injection / Jailbreak）
try:
    from app.core.llm_firewall import PromptInjectionError, prompt_injection_exception_handler
    app.add_exception_handler(PromptInjectionError, prompt_injection_exception_handler)
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(f"LLM 防火牆例外處理器載入失敗（已跳過）: {_e}")

# Pydantic validation error → 中文錯誤訊息
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": {"message": "必要參數未提供"}},
    )


# Generic exception handler — 確保所有未捕捉例外都印 traceback 到 stdout
# 對應 RC2（2026-04-29 cloud QA）：原本 silent server error 沒 traceback 無法 debug
import logging as _err_logging
_err_logger = _err_logging.getLogger("app.main.unhandled")

@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    _err_logger.exception(
        "Unhandled exception at %s %s: %s",
        request.method, request.url.path, exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": {"message": f"Internal Server Error: {type(exc).__name__}"}},
    )

# 靜態檔案：考古題圖像（爬蟲 PyMuPDF 抽出），供題目卡渲染
_hist_dir = Path(__file__).resolve().parent.parent / "data" / "historical_questions"
if _hist_dir.exists():
    app.mount(
        "/static/historical-questions",
        StaticFiles(directory=str(_hist_dir)),
        name="historical-questions",
    )

# 註冊 API 路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
@app.get(f"{settings.API_V1_PREFIX}/health")
def health_check():
    """健康檢查端點。"""
    return {"status": "healthy", "project": settings.PROJECT_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
