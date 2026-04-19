#!/usr/bin/env python3
"""
將爬蟲產生的 JSON 匯入 CertiMate 資料庫（使用 historical_exams 表）

使用方式：
    # Dry-run（不寫入）
    .venv/bin/python -m app.scripts.import_exam_questions \
      --json-dir data/historical_questions --dry-run

    # 實際匯入
    .venv/bin/python -m app.scripts.import_exam_questions \
      --json-dir data/historical_questions

    # 僅匯入指定考試
    .venv/bin/python -m app.scripts.import_exam_questions \
      --json-dir data/historical_questions --exam-code 114010
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models import Base
from app.models.historical_exam import HistoricalExam
from app.models.question import Question

from app.core.config import PUBLIC_B2C_TENANT_ID

settings = get_settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

DEFAULT_TENANT_ID = PUBLIC_B2C_TENANT_ID


class QuestionImporter:
    def __init__(self, db: Session, dry_run: bool = False):
        self.db = db
        self.dry_run = dry_run
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def _find_or_create_historical_exam(
        self,
        exam_code: str,
        category_code: str,
        subject_code: str,
        meta: dict,
        tenant_id: str,
    ) -> HistoricalExam:
        """取得或建立 historical_exams 記錄。"""
        he = (
            self.db.query(HistoricalExam)
            .filter(
                HistoricalExam.exam_code == exam_code,
                HistoricalExam.category_code == category_code,
                HistoricalExam.subject_code == subject_code,
            )
            .first()
        )
        if he:
            return he

        # 從 exam_code 推算年份：前 3 碼 = 民國年
        year = None
        if exam_code and len(exam_code) >= 3:
            try:
                year = int(exam_code[:3])
            except ValueError:
                pass

        he = HistoricalExam(
            id=uuid4(),
            exam_code=exam_code,
            category_code=category_code,
            subject_code=subject_code,
            exam_name=meta.get("exam_name"),
            category_name=meta.get("category_name"),
            subject_name=meta.get("subject_name"),
            source=meta.get("source", "考選部考畢試題查詢平臺"),
            total_questions=meta.get("total_questions"),
            year=year,
            tenant_id=tenant_id,
        )
        self.db.add(he)
        self.db.flush()
        return he

    def import_from_json_file(self, json_file: Path, tenant_id: str = DEFAULT_TENANT_ID) -> bool:
        """從單個 JSON 檔案匯入。"""
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            meta = data.get("import_meta", {})
            questions_data = data.get("questions", [])

            if not questions_data:
                return False

            exam_code = meta.get("exam_code", "")
            category_code = meta.get("category_code", "")
            subject_code = meta.get("subject_code", "")

            # 取得或建立 HistoricalExam
            he = self._find_or_create_historical_exam(
                exam_code, category_code, subject_code, meta, tenant_id
            )

            log.info(
                f"  {exam_code}/{category_code}/{subject_code} "
                f"({len(questions_data)} 題)"
            )

            # Defensive import: ORM add + IntegrityError catch.
            # UNIQUE (historical_exam_id, question_number) index from migration 055
            # guarantees no duplicates. On conflict we skip silently.
            # Note: pg_insert().on_conflict_do_nothing() was tried but fails on
            # production SA 2.0 because session.bind is None (SA 2.0 deprecation).
            from sqlalchemy.exc import IntegrityError

            imported_in_file = 0
            for q_data in questions_data:
                q_num = q_data.get("question_number")

                # Pre-check (fast path — avoids SA object creation for existing rows)
                existing = (
                    self.db.query(Question)
                    .filter(
                        Question.historical_exam_id == he.id,
                        Question.question_number == q_num,
                    )
                    .first()
                )
                if existing:
                    self.skipped_count += 1
                    continue

                question = Question(
                    id=uuid4(),
                    exam_id=None,
                    historical_exam_id=he.id,
                    question_number=q_num,
                    content=q_data.get("content", ""),
                    type=q_data.get("type", "single_choice"),
                    option_a=q_data.get("option_a"),
                    option_b=q_data.get("option_b"),
                    option_c=q_data.get("option_c"),
                    option_d=q_data.get("option_d"),
                    correct_answer=q_data.get("correct_answer", ""),
                    explanation=q_data.get("explanation", ""),
                    bloom_category=q_data.get("bloom_category"),
                    historical_source="moex",
                    source_type="historical",
                    tenant_id=tenant_id,
                )
                try:
                    self.db.add(question)
                    self.db.flush()
                    imported_in_file += 1
                    self.imported_count += 1
                except IntegrityError:
                    self.db.rollback()
                    self.skipped_count += 1

            if not self.dry_run:
                self.db.commit()

            log.info(f"    ✓ 匯入 {imported_in_file} 題")
            return True

        except Exception as e:
            log.error(f"  ✗ 匯入失敗 {json_file}: {e}", exc_info=True)
            self.db.rollback()
            self.error_count += 1
            return False

    def import_directory(
        self, json_dir: Path, exam_code_filter: Optional[str] = None, tenant_id: str = DEFAULT_TENANT_ID
    ):
        """從目錄匯入所有高普考 JSON 檔案。"""
        json_dir = Path(json_dir)
        if not json_dir.exists():
            log.error(f"目錄不存在：{json_dir}")
            return

        log.info(f"掃描目錄：{json_dir}")

        # 掃描所有包含 JSON 的子目錄（排除 _pdf, _catalog 等系統目錄）
        SKIP_DIRS = {"_pdf", "_catalog", "_backup_before_cleanup", "__pycache__"}
        exam_dirs = []
        for d in sorted(json_dir.iterdir()):
            if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith("."):
                if exam_code_filter and d.name != exam_code_filter:
                    continue
                exam_dirs.append(d)

        if not exam_dirs:
            log.warning("未找到符合的考試目錄（格式：6 位數字如 114010）")
            return

        for exam_dir in exam_dirs:
            log.info(f"\n{'='*60}")
            log.info(f"考試：{exam_dir.name}")
            log.info(f"{'='*60}")

            for cat_dir in sorted(exam_dir.iterdir()):
                if not cat_dir.is_dir():
                    continue
                for json_file in sorted(cat_dir.glob("*.json")):
                    self.import_from_json_file(json_file, tenant_id)

        # 摘要
        log.info(f"\n{'='*60}")
        log.info("匯入摘要")
        log.info(f"{'='*60}")
        log.info(f"✓ 成功匯入：{self.imported_count} 題")
        log.info(f"⊘ 已存在（跳過）：{self.skipped_count} 題")
        log.info(f"✗ 失敗：{self.error_count} 個檔案")
        log.info(f"{'🔍 dry-run（未寫入）' if self.dry_run else '✅ 已提交到資料庫'}")


def main():
    parser = argparse.ArgumentParser(description="將爬蟲 JSON 匯入 CertiMate historical_exams + questions")
    parser.add_argument(
        "--json-dir",
        default="data/historical_questions",
        help="JSON 目錄位置",
    )
    parser.add_argument("--exam-code", help="僅匯入指定考試代碼（如 114010）")
    parser.add_argument("--dry-run", action="store_true", help="模擬執行，不寫入資料庫")
    parser.add_argument("--tenant-id", default=DEFAULT_TENANT_ID, help="租戶 ID")

    args = parser.parse_args()

    log.info(f"連接資料庫：{settings.DATABASE_URL}")

    engine = create_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        importer = QuestionImporter(db, dry_run=args.dry_run)
        importer.import_directory(
            Path(args.json_dir),
            exam_code_filter=args.exam_code,
            tenant_id=args.tenant_id,
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
