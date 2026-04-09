#!/usr/bin/env python3
"""將舊格式考古題 JSON 正規化為統一 import_meta 格式。

舊格式（ipas/finance/real_estate）→ 新格式（compatible with import_exam_questions.py）

使用方式：
    python scripts/crawlers/normalize_json.py --dry-run    # 預覽
    python scripts/crawlers/normalize_json.py              # 執行轉換
"""

import argparse
import json
import logging
import re
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "historical_questions"

# 舊格式目錄（排除新格式的 6 位數代碼目錄和系統目錄）
OLD_FORMAT_DIRS = ["ipas", "finance", "real_estate"]

# 來源 → exam_code 對照表（虛擬代碼，用於匯入識別）
SOURCE_CODE_MAP = {
    "ipas": "IPAS00",
    "finance": "FIN000",
    "real_estate": "RE0000",
}


def normalize_file(json_path: Path, dry_run: bool = False) -> bool:
    """正規化單個 JSON 檔案。"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        log.error(f"讀取失敗 {json_path}: {e}")
        return False

    meta = data.get("import_meta", {})

    # 如果已經有 exam_code，跳過（已正規化）
    if "exam_code" in meta:
        return False

    # 推導 exam_code / category_code / subject_code
    rel_path = json_path.relative_to(DATA_DIR)
    parts = list(rel_path.parts)  # e.g., ['ipas', 'big_data', 'xxx.json']

    source_type = parts[0] if parts else "unknown"
    category = parts[1] if len(parts) > 1 else "general"
    subject = json_path.stem  # e.g., '109_bda_beginner_sample_subject1'

    exam_code = SOURCE_CODE_MAP.get(source_type, "UNK000")

    # 嘗試從檔名提取年份
    year_match = re.match(r"(\d{2,3})_", subject)
    year = int(year_match.group(1)) if year_match else meta.get("year", 0)
    if year and year < 200:
        exam_code = f"{source_type[:3].upper()}{year:03d}"

    # 建立統一 meta
    new_meta = {
        "source": meta.get("source_name", f"CertiMate {source_type} 題庫"),
        "exam_code": exam_code,
        "category_code": category,
        "subject_code": subject,
        "exam_name": meta.get("source_name", ""),
        "total_questions": meta.get("total_questions", len(data.get("questions", []))),
        "questions_with_answer": sum(
            1 for q in data.get("questions", []) if q.get("correct_answer")
        ),
        # 保留舊格式的豐富資訊
        "bloom_distribution": meta.get("bloom_distribution"),
        "difficulty_distribution": meta.get("difficulty_distribution"),
        "year": year,
    }

    data["import_meta"] = new_meta

    # 正規化 questions 欄位名稱
    for q in data.get("questions", []):
        # 確保有 type 欄位
        if "type" not in q:
            q["type"] = "single_choice"
        # 確保有 source_type
        if "source_type" not in q:
            q["source_type"] = "historical"

    if dry_run:
        log.info(f"  [DRY-RUN] {json_path.name} → exam_code={exam_code}, "
                 f"category={category}, {new_meta['total_questions']} 題")
        return True

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"  ✓ {json_path.name} → exam_code={exam_code}")
    return True


def main():
    parser = argparse.ArgumentParser(description="正規化舊格式考古題 JSON")
    parser.add_argument("--dry-run", action="store_true", help="預覽不修改")
    args = parser.parse_args()

    converted = 0
    for dir_name in OLD_FORMAT_DIRS:
        dir_path = DATA_DIR / dir_name
        if not dir_path.exists():
            continue

        log.info(f"\n掃描 {dir_name}/")
        for json_file in sorted(dir_path.rglob("*.json")):
            if normalize_file(json_file, dry_run=args.dry_run):
                converted += 1

    log.info(f"\n{'預覽' if args.dry_run else '轉換'}完成：{converted} 個檔案")


if __name__ == "__main__":
    main()
