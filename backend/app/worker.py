"""Celery Worker — 非同步任務處理 + 多租戶優先權佇列.

佇列架構：
    paid_priority  — B2B + ULTRA_1599，確保付費租戶解析任務（OCR/STT）優先執行
    standard       — PRO_199 / PRO_PLUS_399
    background     — FREE（低優先度）
    celery         — 預設佇列（exam_settlement / topology_change）

啟動方式（全佇列）：
    .venv/bin/celery -A app.worker worker --loglevel=info

啟動方式（按佇列水平擴展）：
    .venv/bin/celery -A app.worker worker -Q paid_priority -c 4 --hostname=paid@%h
    .venv/bin/celery -A app.worker worker -Q standard -c 2 --hostname=std@%h
    .venv/bin/celery -A app.worker worker -Q background -c 1 --hostname=bg@%h
    .venv/bin/celery -A app.worker worker -Q celery -c 2 --hostname=default@%h

本地開發需要 Redis：
    docker run -d --name certimate-redis -p 6379:6379 redis:7-alpine
"""

import os
from celery import Celery
from kombu import Queue, Exchange

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# ── 佇列名稱常數（供 tasks 模組 import 使用）────────────────────────────────

QUEUE_PAID_PRIORITY = "paid_priority"
QUEUE_STANDARD = "standard"
QUEUE_BACKGROUND = "background"
QUEUE_DEFAULT = "celery"

# ── Celery App 初始化 ─────────────────────────────────────────────────────────

celery_app = Celery(
    "certimate",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "app.tasks.exam_settlement",
        "app.tasks.topology_change",
        "app.tasks.document_processing",
    ],
)

# ── 佇列定義（優先權 0-9，數字越大優先度越高）────────────────────────────────

_default_exchange = Exchange("certimate", type="direct")

celery_app.conf.task_queues = (
    # 付費優先佇列：B2B + ULTRA，最高優先度
    Queue(
        QUEUE_PAID_PRIORITY,
        _default_exchange,
        routing_key=QUEUE_PAID_PRIORITY,
        queue_arguments={"x-max-priority": 9},
    ),
    # 標準佇列：PRO 方案
    Queue(
        QUEUE_STANDARD,
        _default_exchange,
        routing_key=QUEUE_STANDARD,
        queue_arguments={"x-max-priority": 5},
    ),
    # 背景佇列：免費版
    Queue(
        QUEUE_BACKGROUND,
        _default_exchange,
        routing_key=QUEUE_BACKGROUND,
        queue_arguments={"x-max-priority": 1},
    ),
    # 預設佇列：考試結算、考綱變更等核心任務
    Queue(
        QUEUE_DEFAULT,
        _default_exchange,
        routing_key=QUEUE_DEFAULT,
        queue_arguments={"x-max-priority": 5},
    ),
)

celery_app.conf.task_default_queue = QUEUE_DEFAULT
celery_app.conf.task_default_exchange = "certimate"
celery_app.conf.task_default_routing_key = QUEUE_DEFAULT

# ── 任務路由規則 ────────────────────────────────────────────────────────────

celery_app.conf.task_routes = {
    # 文件解析系列 → 由 dispatch_*() helper 依方案動態分配佇列
    # 此處設定 fallback 路由（若直接 .delay() 未指定 queue）
    "app.tasks.document_processing.parse_document_task":   {"queue": QUEUE_BACKGROUND},
    "app.tasks.document_processing.ocr_image_task":        {"queue": QUEUE_BACKGROUND},
    "app.tasks.document_processing.transcribe_audio_task": {"queue": QUEUE_BACKGROUND},
    # 考試結算 → 預設佇列（即時性要求）
    "app.tasks.exam_settlement.settle_exam":               {"queue": QUEUE_DEFAULT},
    # 考綱變更 fan-out → 背景佇列
    "app.tasks.topology_change.master_topology_change":    {"queue": QUEUE_BACKGROUND},
    "app.tasks.topology_change.batch_recalculate_progress": {"queue": QUEUE_BACKGROUND},
}

# ── 全域配置 ─────────────────────────────────────────────────────────────────

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Taipei",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # 公平分配，避免饑餓
    # 結果過期（1 天）
    result_expires=86400,
    # Worker 最大任務數（防記憶體洩漏）
    worker_max_tasks_per_child=500,
)
