"""考綱變更 Fan-out 任務 — V3 批次重算防 N+1 寫入風暴.

當考綱新增/刪除考點時：
1. Master Task 撈出所有訂閱該考科的使用者
2. 切塊（每 500 人）派發 Sub-Task
3. Sub-Task 在記憶體內重算 → 批次更新 DB
"""

import logging
import uuid
from typing import Optional

from app.worker import celery_app

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500


@celery_app.task(bind=True)
def master_topology_change(self, root_topic_id: str, change_type: str = "expand"):
    """Master Task：派發 Fan-out 子任務。"""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 找出所有有此考科 mastery 的使用者
        result = db.execute(text("""
            SELECT DISTINCT user_id FROM node_mastery
            WHERE node_id IN (
                SELECT id FROM knowledge_nodes
                WHERE parent_id = :root OR id = :root
            )
        """), {"root": root_topic_id})

        user_ids = [str(row[0]) for row in result]
        logger.info("Topology change: %d users affected for root %s", len(user_ids), root_topic_id)

        # 切塊派發
        for i in range(0, len(user_ids), CHUNK_SIZE):
            chunk = user_ids[i:i + CHUNK_SIZE]
            batch_recalculate_progress.delay(chunk, root_topic_id, change_type)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def batch_recalculate_progress(
    self,
    user_ids_chunk: list[str],
    root_topic_id: str,
    change_type: str = "expand",
):
    """Sub-Task：批次重算一組使用者的進度。"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.services.organic_progress import OrganicProgressEngine

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        progress_engine = OrganicProgressEngine(db)

        for user_id in user_ids_chunk:
            try:
                progress_engine.propagate_upward(user_id, root_topic_id)
            except Exception as e:
                logger.warning("Failed to recalculate for user %s: %s", user_id, e)

        db.commit()
        logger.info("Batch recalculated %d users for root %s", len(user_ids_chunk), root_topic_id)

    except Exception as exc:
        db.rollback()
        logger.error("Batch recalculate failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)
    finally:
        db.close()
