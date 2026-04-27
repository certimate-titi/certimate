#!/usr/bin/env python3
"""歷史考試 SM-2 重播 — 從考試記錄重建 base_mastery 和 ease_factor.

使用方式：
    # Dry-run
    .venv/bin/python -m app.scripts.replay_exam_history --dry-run

    # 正式執行
    .venv/bin/python -m app.scripts.replay_exam_history
"""

import argparse
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.answer import Answer
from app.models.exam import Exam, ExamStatus
from app.models.question import Question
from app.models.node_mastery import NodeMastery
from app.services.sm2_engine import SM2Engine, TopicState

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def main():
    """CLI 進入點：依時間順序重播所有 SUBMITTED 考試重建 SM-2 狀態。

    流程：
        1. 抓取 ``Exam.status == SUBMITTED`` 的考試，依 ``submitted_at`` 排
           序，可用 ``--user-id`` 過濾單一使用者。
        2. 按使用者分組，每場考試把答案依 ``Question.node_id`` 聚合，丟給
           :class:`SM2Engine` 計算新的 ``base_mastery`` / ``ease_factor`` /
           ``last_tested_at`` / ``next_review_at`` / ``status``。
        3. 將計算結果寫回 ``node_mastery`` 表。

    副作用：
        非 dry-run 模式會 ``UPDATE node_mastery``；dry-run 則 rollback。
    """
    parser = argparse.ArgumentParser(description="歷史考試 SM-2 重播")
    parser.add_argument("--dry-run", action="store_true", help="不寫入 DB")
    parser.add_argument("--user-id", help="僅處理指定使用者")
    args = parser.parse_args()

    engine_db = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine_db)
    db = Session()
    sm2 = SM2Engine()

    try:
        # 取得所有已提交的考試（按時間排序）
        query = db.query(Exam).filter(Exam.status == ExamStatus.SUBMITTED)
        if args.user_id:
            query = query.filter(Exam.user_id == uuid.UUID(args.user_id))
        exams = query.order_by(Exam.submitted_at.asc().nullslast(), Exam.created_at.asc()).all()

        log.info(f"找到 {len(exams)} 場已提交考試")

        # 按使用者分組
        user_exams: dict[str, list] = {}
        for exam in exams:
            uid = str(exam.user_id)
            user_exams.setdefault(uid, []).append(exam)

        total_updated = 0

        for uid, exams_list in user_exams.items():
            user_uuid = uuid.UUID(uid)

            # 載入現有 mastery（重置為初始值）
            masteries = db.query(NodeMastery).filter(NodeMastery.user_id == user_uuid).all()
            mastery_map = {str(m.node_id): m for m in masteries}

            # 追蹤每個 topic 的狀態（從零開始重建）
            topic_states: dict[str, TopicState] = {}

            for exam in exams_list:
                exam_time = exam.submitted_at or exam.created_at or datetime.now(timezone.utc)

                # 取得此考試的所有答案
                answers = db.query(Answer).filter(Answer.exam_id == exam.id).all()

                # 按 node_id 分組
                topic_answers: dict[str, list[bool]] = {}
                for a in answers:
                    q = db.query(Question).filter(Question.id == a.question_id).first()
                    if q and q.node_id:
                        nid = str(q.node_id)
                        topic_answers.setdefault(nid, []).append(bool(a.is_correct))

                if not topic_answers:
                    continue

                # SM-2 批次處理
                updated = sm2.process_exam_answers(topic_answers, topic_states, exam_time)
                topic_states.update(updated)

            # 寫回 DB
            updated_count = 0
            for nid, state in topic_states.items():
                m = mastery_map.get(nid)
                if m:
                    m.base_mastery = state.base_mastery
                    m.ease_factor = state.ease_factor
                    m.last_tested_at = state.last_tested_at
                    m.next_review_at = state.next_review_at
                    m.status = state.status
                    m.mastery_rate = round(state.base_mastery * 100, 2)
                    m.color = {"MASTERED": "green", "PENDING": "yellow", "CRITICAL": "red"}.get(state.status, "gray")
                    updated_count += 1

            total_updated += updated_count
            log.info(f"  使用者 {uid[:8]}...: {len(exams_list)} 場考試 → {updated_count} 個節點更新")

        if args.dry_run:
            log.info(f"\n🔍 dry-run — 未寫入 DB (共 {total_updated} 個節點)")
            db.rollback()
        else:
            db.commit()
            log.info(f"\n✅ SM-2 重播完成: {total_updated} 個節點已更新")

    except Exception as e:
        db.rollback()
        log.error(f"重播失敗: {e}", exc_info=True)
    finally:
        db.close()


if __name__ == "__main__":
    main()
