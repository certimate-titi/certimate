"""
CertiMate 考古題批次匯入腳本

從 backend/data/historical_questions/ 目錄讀取所有 JSON，
為每份試卷建立一個系統 Exam 記錄 + 批次 INSERT questions。

用法:
    cd backend
    python scripts/import_historical_questions.py

前置條件:
    - 已執行 alembic upgrade head（含 migration 021 + 022）
    - DB 已有 subject_categories / subjects seed 資料
"""
import json
import os
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.exam import Exam, ExamStatus
from app.models.question import Question

# ── 科目代碼 → DB subject UUID 映射（與 migration 021 一致）──
SUBJECT_UUID_MAP = {
    "finance/securities": "b0000001-0002-0000-0000-000000000002",
    "finance/derivatives": "b0000001-0004-0000-0000-000000000004",
    "finance/anti_money_laundering": "b0000001-0005-0000-0000-000000000005",
    "finance/financial_planning": "b0000001-0006-0000-0000-000000000006",
    "finance/trust": "b0000001-0001-0000-0000-000000000001",
    "finance/insurance": "b0000001-0003-0000-0000-000000000003",
    "real_estate/broker": "b0000002-0001-0000-0000-000000000001",
    "real_estate/land_agent": "b0000002-0002-0000-0000-000000000002",
    "real_estate/appraiser": "b0000002-0003-0000-0000-000000000003",
    "ipas/ai_planner": "b0000003-0001-0000-0000-000000000001",
    "ipas/big_data": "b0000003-0002-0000-0000-000000000002",
    "ipas/iot": "b0000003-0003-0000-0000-000000000003",
    "ipas/blockchain": "b0000003-0004-0000-0000-000000000004",
    "ipas/information_security": "b0000003-0005-0000-0000-000000000005",
}

# 系統用戶 UUID（用於建立題庫 exam，不綁定真實用戶）
SYSTEM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

# 難度映射
BLOOM_TO_DIFFICULTY = {
    "remember": "easy",
    "understand": "easy",
    "apply": "medium",
    "analyze": "hard",
    "evaluate": "hard",
    "create": "hard",
}


def get_subject_uuid(json_path: str, base_dir: str) -> str:
    """從 JSON 檔案路徑推導 subject UUID"""
    rel = os.path.relpath(os.path.dirname(json_path), base_dir)
    # rel = "finance/securities" or "ipas/ai_planner" etc.
    return SUBJECT_UUID_MAP.get(rel, "")


def import_json(session, json_path: str, base_dir: str, dry_run: bool = False):
    """匯入一份 JSON 試卷"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    meta = data["import_meta"]
    questions = data["questions"]

    if not questions:
        return 0

    subject_uuid = get_subject_uuid(json_path, base_dir)
    if not subject_uuid:
        print(f"  ⚠️  跳過（無法映射 subject）: {json_path}")
        return 0

    # 建立歷史來源標記
    source_name = meta.get("source_name", "")
    historical_source = f"{meta.get('year', '')}年第{meta.get('session', '')}次 {source_name}"

    # 檢查是否已匯入（用 historical_source 去重）
    existing = session.execute(
        text("SELECT id FROM exams WHERE institution_assignment_id IS NULL "
             "AND subject_id = :sid "
             "AND total_questions = :total "
             "LIMIT 1"),
        {"sid": subject_uuid, "total": len(questions)}
    ).fetchone()

    # 用更精確的方式檢查：看 questions 表有沒有相同 historical_source
    existing_qs = session.execute(
        text("SELECT COUNT(*) FROM questions WHERE historical_source = :hs"),
        {"hs": historical_source}
    ).scalar()

    if existing_qs and existing_qs > 0:
        print(f"  ⏭️  已存在（{existing_qs} 題）: {historical_source}")
        return 0

    if dry_run:
        print(f"  🔍 DRY RUN: 會匯入 {len(questions)} 題 | {historical_source}")
        return len(questions)

    # 確保系統用戶存在
    sys_user = session.execute(
        text("SELECT id FROM users WHERE id = :uid"),
        {"uid": str(SYSTEM_USER_ID)}
    ).fetchone()
    if not sys_user:
        session.execute(
            text("INSERT INTO users (id, email, password_hash, display_name, role) "
                 "VALUES (:id, :email, :pw, :name, :role) "
                 "ON CONFLICT (id) DO NOTHING"),
            {
                "id": str(SYSTEM_USER_ID),
                "email": "system@certimate.app",
                "pw": "SYSTEM_NO_LOGIN",
                "name": "系統題庫",
                "role": "admin",
            }
        )

    # 建立 Exam 記錄
    exam_id = uuid.uuid4()
    bloom_dist = meta.get("bloom_distribution", {})
    diff_dist = meta.get("difficulty_distribution", {})

    session.execute(
        text("""
            INSERT INTO exams (id, user_id, subject_id, status, total_questions,
                               difficulty_distribution, bloom_distribution, score, correct_count)
            VALUES (:id, :user_id, :subject_id, :status, :total,
                    :diff_dist, :bloom_dist, NULL, NULL)
        """),
        {
            "id": str(exam_id),
            "user_id": str(SYSTEM_USER_ID),
            "subject_id": subject_uuid,
            "status": "SUBMITTED",
            "total": len(questions),
            "diff_dist": json.dumps(diff_dist),
            "bloom_dist": json.dumps(bloom_dist),
        }
    )

    # 批次 INSERT questions
    for q in questions:
        bloom = q.get("bloom_category", "remember")
        difficulty = BLOOM_TO_DIFFICULTY.get(bloom, "medium")
        correct = q.get("correct_answer", "")
        if not correct:
            correct = "N/A"

        session.execute(
            text("""
                INSERT INTO questions (id, exam_id, question_number, type, difficulty,
                                       bloom_category, content, option_a, option_b,
                                       option_c, option_d, correct_answer,
                                       explanation, historical_source)
                VALUES (:id, :exam_id, :qnum, :qtype, :diff,
                        :bloom, :content, :oa, :ob, :oc, :od, :answer,
                        :explanation, :hsource)
            """),
            {
                "id": str(uuid.uuid4()),
                "exam_id": str(exam_id),
                "qnum": q["question_number"],
                "qtype": q.get("type", "single_choice"),
                "diff": difficulty,
                "bloom": bloom,
                "content": q["content"],
                "oa": q.get("option_a", ""),
                "ob": q.get("option_b", ""),
                "oc": q.get("option_c", ""),
                "od": q.get("option_d", ""),
                "answer": correct,
                "explanation": q.get("explanation", ""),
                "hsource": historical_source,
            }
        )

    session.commit()
    return len(questions)


def main():
    dry_run = "--dry-run" in sys.argv

    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "data", "historical_questions"
    )
    base_dir = os.path.abspath(base_dir)

    if not os.path.exists(base_dir):
        print(f"❌ 找不到目錄: {base_dir}")
        sys.exit(1)

    # 收集所有 JSON
    json_files = []
    for root, dirs, files in sorted(os.walk(base_dir)):
        for f in sorted(files):
            if f.endswith(".json") and f != "catalog.json":
                json_files.append(os.path.join(root, f))

    print(f"=== CertiMate 考古題匯入 {'(DRY RUN)' if dry_run else ''} ===")
    print(f"找到 {len(json_files)} 份 JSON\n")

    # DB 連線
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    total_imported = 0
    total_skipped = 0

    try:
        for jf in json_files:
            rel = os.path.relpath(jf, base_dir)
            count = import_json(session, jf, base_dir, dry_run=dry_run)
            if count > 0:
                print(f"  ✅ {count:>4} 題 | {rel}")
                total_imported += count
            else:
                total_skipped += 1
    except Exception as e:
        session.rollback()
        print(f"\n❌ 錯誤: {e}")
        raise
    finally:
        session.close()

    print(f"\n{'='*50}")
    print(f"匯入: {total_imported} 題 | 跳過: {total_skipped} 份")
    if dry_run:
        print("(DRY RUN — 未實際寫入 DB)")


if __name__ == "__main__":
    main()
