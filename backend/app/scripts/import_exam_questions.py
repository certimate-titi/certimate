#!/usr/bin/env python3
"""考古題 JSON 匯入 CLI。

掃描 ``data/historical_questions/`` 目錄下的 JSON 檔，建立或復用
``historical_exams`` 紀錄，並把題目寫入 ``questions``（``source_type
='historical'``、``historical_source='moex'``）。對 ``(historical_exam_id,
question_number)`` 已存在的題目以 ``IntegrityError`` 為 fallback 跳過。

Usage:
    # Dry-run（不寫入）
    .venv/bin/python -m app.scripts.import_exam_questions \\
        --json-dir data/historical_questions --dry-run

    # 實際匯入
    .venv/bin/python -m app.scripts.import_exam_questions \\
        --json-dir data/historical_questions

    # 僅匯入指定考試
    .venv/bin/python -m app.scripts.import_exam_questions \\
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
    """考古題 JSON 批次匯入器。

    封裝 ``historical_exams`` upsert 與 ``questions`` 防重複插入邏輯，並維護
    匯入計數（成功 / 跳過 / 失敗）供 CLI 摘要使用。

    Attributes:
        db: SQLAlchemy Session（呼叫端負責生命週期）。
        dry_run: 若為 True，不執行 ``commit``，僅記錄 log。
        imported_count: 累計成功匯入題數。
        skipped_count: 累計因已存在而跳過的題數。
        error_count: 累計處理失敗的 JSON 檔數。
    """

    def __init__(self, db: Session, dry_run: bool = False):
        """初始化匯入器。

        Args:
            db: SQLAlchemy Session。
            dry_run: 是否為模擬執行（True 不寫入 DB）。
        """
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
        """以 ``(exam_code, category_code, subject_code)`` 為鍵 upsert ``historical_exams``。

        Args:
            exam_code: 考試代碼（例：``114010``）。前 3 碼會被推算為民國年。
            category_code: 類科代碼。
            subject_code: 科目代碼。
            meta: JSON 檔的 ``import_meta`` 區段，提供考試 / 類科 / 科目名
                稱、題數、來源等補充欄位。
            tenant_id: 租戶 UUID（預設 ``public_b2c``）。

        Returns:
            既存或新建立的 ``HistoricalExam`` 實例。

        副作用：
            找不到對應紀錄時會 ``db.add`` + ``db.flush()`` 寫入新列。
        """
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
        """從單個爬蟲產出的 JSON 檔匯入題目。

        Args:
            json_file: JSON 檔路徑，須包含 ``import_meta`` 與 ``questions``
                兩個頂層 key。
            tenant_id: 租戶 UUID（預設 ``public_b2c``）。

        Returns:
            是否成功處理該檔案（``False`` 表示無題目或發生例外）。

        副作用：
            - upsert ``historical_exams``。
            - 對 ``questions`` 表寫入新題；衝突 ``(historical_exam_id,
              question_number)`` 時走 ``IntegrityError`` 跳過。
            - 非 dry-run 模式於檔案結束時 ``commit``。
        """
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
                    figure_urls=[
                        f"/static/historical-questions/{exam_code}/{category_code}/{p}"
                        if not p.startswith(("/", "http"))
                        else p
                        for p in (q_data.get("figure_urls") or [])
                    ],
                    figure_description=q_data.get("figure_description") or None,
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
        """遞迴掃描目錄並匯入所有 JSON 檔。

        目錄結構為 ``{exam_code}/{category_code}/*.json``；會略過 ``_pdf``、
        ``_catalog``、``_backup_before_cleanup``、``__pycache__`` 等系統目錄
        與 dotfile。

        Args:
            json_dir: 考古題 JSON 根目錄。
            exam_code_filter: 若提供，只處理 ``{exam_code}`` 等於此值的子目
                錄；其餘略過。
            tenant_id: 租戶 UUID（預設 ``public_b2c``）。

        副作用：
            走訪每個 JSON 檔呼叫 :meth:`import_from_json_file`，並在結束時
            把 ``imported_count`` / ``skipped_count`` / ``error_count`` 摘要
            輸出到 log。
        """
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
    """CLI 進入點：解析參數、建立 DB Session、執行 :class:`QuestionImporter`。

    副作用：
        建立 SQLAlchemy engine 並開啟 Session；非 dry-run 模式下會把考古題
        寫入 ``historical_exams`` 與 ``questions`` 兩張表。
    """
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
