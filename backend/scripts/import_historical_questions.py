"""
CertiMate 考古題批次匯入腳本

從 exam-bank/data/json/ 讀取驗證通過的 JSON，
為每份試卷建立一個系統 Exam 記錄 + 批次 INSERT questions。

用法:
    cd backend
    python scripts/import_historical_questions.py          # 正式匯入
    python scripts/import_historical_questions.py --dry-run # 預覽

前置條件:
    - 已執行 alembic upgrade head（含 migration 021-024）
    - DB 已有 subject_categories / subjects seed 資料
"""
import json
import os
import re
import sys
import uuid
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
settings = get_settings()

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

# 來源名稱映射
SOURCE_NAME_MAP = {
    "securities_salesperson": "證券商業務員",
    "securities_regulations_b": "證券商高級業務員法規",
    "senior_securities": "證券商高級業務員",
    "internal_control": "證券商內部控制",
    "futures_analyst": "期貨交易分析人員",
    "futures_salesperson": "期貨商業務員",
    "futures_trust_fund": "期貨信託基金",
    "investment_trust": "投信投顧業務員",
    "investment_regulations_b": "投信投顧法規",
    "aml_cft": "防制洗錢與打擊資恐",
    "sustainability": "永續金融",
    "broker_regulations": "不動產經紀人法規",
}


def derive_historical_source(json_filename: str, rel_dir: str) -> str:
    """從 JSON 檔名推導歷史來源標記"""
    stem = Path(json_filename).stem  # e.g. "securities_salesperson_session01_questions"

    # 嘗試提取年份（3 位民國年）
    year_match = re.search(r'(\d{3})_', stem)
    year = f"民國{year_match.group(1)}年" if year_match else ""

    # 嘗試提取 session
    session_match = re.search(r'session(\d+)', stem)
    session = f"第{session_match.group(1)}次" if session_match else ""

    # 來源名稱
    source_name = ""
    for key, name in SOURCE_NAME_MAP.items():
        if key in stem:
            source_name = name
            break

    if not source_name:
        # Fallback: 用檔名（去掉年份和 _q 後綴）作為來源名稱
        fallback = re.sub(r'^\d{3}_', '', stem)  # remove leading year
        fallback = re.sub(r'_q$|_questions$', '', fallback)  # remove suffixes
        source_name = fallback.replace("_", " ")

    parts = [p for p in [year, session, source_name] if p]
    return " ".join(parts) if parts else stem


def import_json(session, json_path: str, base_dir: str, dry_run: bool = False):
    """匯入一份 JSON 試卷"""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("import_meta", {})
    questions = data.get("questions", [])

    # 只匯入有答案的題目
    valid_questions = [
        q for q in questions
        if q.get("correct_answer") in ("A", "B", "C", "D")
    ]

    if not valid_questions:
        return 0

    rel_dir = os.path.relpath(os.path.dirname(json_path), base_dir)
    subject_uuid = SUBJECT_UUID_MAP.get(rel_dir, "")
    if not subject_uuid:
        print(f"  ⚠️  跳過（無法映射 subject）: {rel_dir}")
        return 0

    # 建立歷史來源標記
    historical_source = derive_historical_source(
        os.path.basename(json_path), rel_dir
    )

    quality_flag = meta.get("quality_flag", "ok")

    if dry_run:
        print(f"  🔍 DRY RUN: {len(valid_questions):>3} 題 [{quality_flag}] | {historical_source}")
        return len(valid_questions)

    # 檢查是否已匯入（用 historical_source 去重）
    existing_qs = session.execute(
        text("SELECT COUNT(*) FROM questions WHERE historical_source = :hs"),
        {"hs": historical_source}
    ).scalar()

    if existing_qs and existing_qs > 0:
        print(f"  ⏭️  已存在（{existing_qs} 題）: {historical_source}")
        return 0

    # 確保系統用戶存在
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

    session.execute(
        text("""
            INSERT INTO exams (id, user_id, subject_id, status, total_questions,
                               score, correct_count)
            VALUES (:id, :user_id, :subject_id, :status, :total, NULL, NULL)
        """),
        {
            "id": str(exam_id),
            "user_id": str(SYSTEM_USER_ID),
            "subject_id": subject_uuid,
            "status": "SUBMITTED",
            "total": len(valid_questions),
        }
    )

    # 批次 INSERT questions
    for q in valid_questions:
        bloom = q.get("bloom_category", "remember")
        difficulty = BLOOM_TO_DIFFICULTY.get(bloom, "medium")

        session.execute(
            text("""
                INSERT INTO questions (id, exam_id, question_number, type, difficulty,
                                       bloom_category, content, option_a, option_b,
                                       option_c, option_d, correct_answer,
                                       explanation, historical_source,
                                       quality_flag, validation_model)
                VALUES (:id, :exam_id, :qnum, :qtype, :diff,
                        :bloom, :content, :oa, :ob, :oc, :od, :answer,
                        :explanation, :hsource,
                        :qflag, :vmodel)
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
                "answer": q["correct_answer"],
                "explanation": q.get("explanation", ""),
                "hsource": historical_source,
                "qflag": quality_flag,
                "vmodel": meta.get("model", ""),
            }
        )

    session.commit()
    return len(valid_questions)


def main():
    dry_run = "--dry-run" in sys.argv

    # 從 exam-bank/data/json/ 讀取
    base_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "exam-bank", "data", "json"
    )
    base_dir = os.path.abspath(base_dir)

    # 載入 manifest 檢查品質
    manifest_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "exam-bank", "data", "convert_manifest.json"
    )

    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)

    if not os.path.exists(base_dir):
        print(f"❌ 找不到目錄: {base_dir}")
        sys.exit(1)

    # 收集所有 JSON（只匯入 quality_flag=ok 的）
    json_files = []
    skipped_quality = 0
    for root, dirs, files in sorted(os.walk(base_dir)):
        for f in sorted(files):
            if not f.endswith(".json"):
                continue

            json_path = os.path.join(root, f)
            rel_dir = os.path.relpath(root, base_dir)

            # 對照 manifest 找品質標記
            manifest_key = f"{rel_dir}/{f.replace('.json', '.pdf')}"
            entry = manifest.get(manifest_key, {})
            qflag = entry.get("quality_flag", "unknown")
            valid_q = entry.get("questions", 0)

            if valid_q == 0:
                skipped_quality += 1
                continue

            json_files.append(json_path)

    print(f"=== CertiMate 考古題匯入 {'(DRY RUN)' if dry_run else ''} ===")
    print(f"找到 {len(json_files)} 份有效 JSON（跳過 {skipped_quality} 份無有效題目）\n")

    if not dry_run:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()
    else:
        db_session = None

    total_imported = 0
    total_skipped = 0

    try:
        for jf in json_files:
            rel = os.path.relpath(jf, base_dir)
            count = import_json(db_session, jf, base_dir, dry_run=dry_run)
            if count > 0:
                print(f"  ✅ {count:>4} 題 | {rel}")
                total_imported += count
            else:
                total_skipped += 1
    except Exception as e:
        if db_session:
            db_session.rollback()
        print(f"\n❌ 錯誤: {e}")
        raise
    finally:
        if db_session:
            db_session.close()

    print(f"\n{'='*50}")
    print(f"匯入: {total_imported} 題 | 跳過: {total_skipped} 份")
    if dry_run:
        print("(DRY RUN — 未實際寫入 DB)")


if __name__ == "__main__":
    main()
