"""OpenTelemetry 全鏈路追蹤模組 — 多租戶 Trace_ID 追蹤.

功能：
1. 自動 Instrument FastAPI 與 SQLAlchemy（每個請求產生 Span）
2. 將 tenant_id 注入每個 Span 的 attribute，實現跨服務資源追蹤
3. OTLP exporter（gRPC）— 預設輸出至 localhost:4317（可覆蓋）
4. 在 OTEL_ENABLED=false 或套件未安裝時，優雅降級（NoOp）

環境變數：
    OTEL_ENABLED             啟用追蹤（預設 "false"，避免無 collector 時錯誤）
    OTEL_SERVICE_NAME        服務名稱（預設 "certimate-api"）
    OTEL_EXPORTER_OTLP_ENDPOINT  OTLP gRPC endpoint（預設 "http://localhost:4317"）
    OTEL_EXPORTER_TYPE       "otlp" | "console"（預設 "otlp"；console 適合本機 debug）

整合建議：
    - 搭配 Grafana Tempo（OTLP 接收端）或 Jaeger（UI 視覺化）
    - 使用 opentelemetry-instrumentation-fastapi 自動產生 HTTP span
    - 搭配 opentelemetry-instrumentation-sqlalchemy 追蹤 DB 查詢耗時
    - 安裝依賴：pip install opentelemetry-distro opentelemetry-exporter-otlp-proto-grpc
               opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-sqlalchemy

使用方式：
    from app.core.telemetry import setup_telemetry, get_tracer, add_tenant_attribute

    # main.py lifespan 中初始化
    setup_telemetry(app)

    # 在 service 層手動建立 Span
    tracer = get_tracer("my_service")
    with tracer.start_as_current_span("process_exam") as span:
        add_tenant_attribute(span, tenant_id)
        ...
"""

import os
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# ── 全域 tracer（懶載入）──────────────────────────────────────────────────
_tracer = None
_otel_available = False
_initialized = False


def _is_enabled() -> bool:
    """判斷 OTel 是否啟用（環境變數控制）。"""
    return os.environ.get("OTEL_ENABLED", "false").lower() in ("true", "1", "yes")


def setup_telemetry(app: "FastAPI") -> None:
    """初始化 OpenTelemetry，並 instrument FastAPI + SQLAlchemy。

    應在 FastAPI lifespan 或 startup 事件中呼叫。
    未安裝 opentelemetry 套件或 OTEL_ENABLED=false 時，此函式為 NoOp。
    """
    global _tracer, _otel_available, _initialized

    if _initialized:
        return

    if not _is_enabled():
        logger.info("OpenTelemetry 追蹤已停用（OTEL_ENABLED=false）")
        _initialized = True
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME

        service_name = os.environ.get("OTEL_SERVICE_NAME", "certimate-api")
        resource = Resource.create({SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)

        # ── Exporter 選擇 ───────────────────────────────────────────────
        exporter_type = os.environ.get("OTEL_EXPORTER_TYPE", "otlp").lower()

        if exporter_type == "console":
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()
            logger.info("OTel Exporter: Console（開發模式）")
        else:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter,
                )
                endpoint = os.environ.get(
                    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"
                )
                exporter = OTLPSpanExporter(endpoint=endpoint)
                logger.info(f"OTel Exporter: OTLP → {endpoint}")
            except ImportError:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter
                exporter = ConsoleSpanExporter()
                logger.warning(
                    "opentelemetry-exporter-otlp-proto-grpc 未安裝，"
                    "降級為 Console exporter"
                )

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(__name__)
        _otel_available = True

        # ── FastAPI 自動 Instrument ─────────────────────────────────────
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(
                app,
                server_request_hook=_request_hook,
                client_response_hook=_response_hook,
            )
            logger.info("✅ FastAPI OpenTelemetry Instrumentor 已啟用")
        except ImportError:
            logger.warning(
                "opentelemetry-instrumentation-fastapi 未安裝，"
                "HTTP span 自動生成停用"
            )

        # ── SQLAlchemy 自動 Instrument ──────────────────────────────────
        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument()
            logger.info("✅ SQLAlchemy OpenTelemetry Instrumentor 已啟用")
        except ImportError:
            logger.warning(
                "opentelemetry-instrumentation-sqlalchemy 未安裝，"
                "DB query span 停用"
            )

        logger.info(
            f"✅ OpenTelemetry 全鏈路追蹤已啟用（service={service_name}）"
        )

    except ImportError:
        logger.warning(
            "opentelemetry 套件未安裝，追蹤功能停用。\n"
            "安裝指令: pip install opentelemetry-distro "
            "opentelemetry-exporter-otlp-proto-grpc "
            "opentelemetry-instrumentation-fastapi "
            "opentelemetry-instrumentation-sqlalchemy"
        )
    except Exception as e:
        logger.error(f"OpenTelemetry 初始化失敗：{e}")
    finally:
        _initialized = True


def _request_hook(span, scope):
    """FastAPI 請求 Hook — 自動注入 tenant_id 至 Span。"""
    if span is None or not span.is_recording():
        return
    # 從 ASGI scope 的 state 取得 tenant_id（若 RLS middleware 已設定）
    request_state = scope.get("state", {})
    tenant_id = getattr(request_state, "tenant_id", None)
    if tenant_id:
        span.set_attribute("certimate.tenant_id", str(tenant_id))


def _response_hook(span, message):
    """FastAPI 回應 Hook — 記錄回應狀態碼。"""
    if span is None or not span.is_recording():
        return
    status_code = message.get("status", 0)
    if status_code >= 400:
        span.set_attribute("http.error", True)


def get_tracer(name: str = "certimate"):
    """取得 Tracer 實例（OTel 未啟用時回傳 NoOp tracer）。"""
    global _tracer, _otel_available
    if not _otel_available or not _is_enabled():
        return _NoOpTracer()
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except Exception:
        return _NoOpTracer()


def add_tenant_attribute(span, tenant_id: Optional[str]) -> None:
    """將 tenant_id 加入 Span attribute（便利函式）。"""
    if span is None or tenant_id is None:
        return
    try:
        if hasattr(span, "is_recording") and span.is_recording():
            span.set_attribute("certimate.tenant_id", str(tenant_id))
    except Exception:
        pass


def record_llm_usage(
    span,
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    tenant_id: Optional[str] = None,
) -> None:
    """記錄 LLM API 使用量至 Span（OKR O3 KR1：LLM 成本追蹤）。"""
    if span is None:
        return
    try:
        if hasattr(span, "is_recording") and span.is_recording():
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.input_tokens", input_tokens)
            span.set_attribute("llm.output_tokens", output_tokens)
            span.set_attribute("llm.total_tokens", input_tokens + output_tokens)
            if tenant_id:
                span.set_attribute("certimate.tenant_id", str(tenant_id))
    except Exception:
        pass


# ── NoOp Tracer（OTel 未啟用時的替代品）─────────────────────────────────

class _NoOpSpan:
    """無操作 Span，OTel 停用時使用。"""
    def is_recording(self): return False
    def set_attribute(self, *a, **kw): pass
    def add_event(self, *a, **kw): pass
    def set_status(self, *a, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass


class _NoOpTracer:
    """無操作 Tracer，OTel 停用時使用。"""
    def start_as_current_span(self, name: str, **kw):
        return _NoOpSpan()

    def start_span(self, name: str, **kw):
        return _NoOpSpan()
