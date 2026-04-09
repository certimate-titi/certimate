"""Celery Worker — 非同步任務處理.

啟動方式：
    .venv/bin/celery -A app.worker worker --loglevel=info

本地開發需要 Redis：
    docker run -d --name certimate-redis -p 6379:6379 redis:7-alpine
"""

import os
from celery import Celery

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "certimate",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks.exam_settlement"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Taipei",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
