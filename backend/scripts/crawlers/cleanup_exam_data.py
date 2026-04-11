#!/usr/bin/env python3
"""
考古題資料清理腳本

問題：
1. 共用科目（國文、法學知識與英文）被複製到每個類科目錄，導致 362 個重複檔案
2. 396 個檔案缺少 exam_name，441 個缺少 subject_name
3. 9 個檔案無答案、2 個空檔案

解決：
1. 去重：共用科目只保留一份，移到 _shared/ 目錄
2. 補全 metadata：填入 exam_name 和 subject_name
3. 清理：移除空檔案，標記無答案檔案

使用方式：
    python3 scripts/crawlers/cleanup_exam_data.py --dry-run   # 預覽
    python3 scripts/crawlers/cleanup_exam_data.py             # 執行
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "historical_questions"
BACKUP_DIR = DATA_DIR / "_backup_before_cleanup"

# ── 科目名稱對照表 ─────────────────────────────────────────────

# 考選部 MOEX — 共用科目代碼 → 科目名稱
MOEX_SUBJECT_NAMES = {
    # 初等考試共用科目
    "0101": "國文",
    "0102": "公民與英文",
    # 高考三級共用科目 (使用同代碼 0101)
    # 普考共用科目 (使用 0102)
    # 初等專業科目
    "0202": "法學大意",
    "0203": "行政學大意",
    "0204": "經濟學大意",
    "0205": "政治學大意",
    "0206": "財政學大意",
    "0301": "地方自治大意",
    "0302": "人事行政大意",
    "0303": "社會工作大意",
    "0304": "教育學大意",
    "0305": "勞工行政大意",
    "0401": "會計學大意",
    "0402": "統計學大意",
    "0403": "稅務法規大意",
    "0404": "財政學大意",
    "0405": "經濟學大意",
    "0406": "會計審計法規大意",
    "0501": "土地法大意",
    "0502": "交通行政大意",
    "0503": "土地行政大意",
    "0504": "運輸學大意",
    "0505": "圖書館學大意",
    "0506": "電子計算機概要",
    # 高考三級科目
    # 0101: 國文（作文與測驗）— 同上
    # 0401: 法學知識與英文
    # 普考科目
    # 0102: 國文（作文與測驗）— 同上
    # 0402: 法學知識與英文
    # 高考/普考專業科目
    "0307": "地方自治法規概要",
    "0308": "地方自治法規概要",
    "0309": "民法總則與親屬編",
    "0410": "民法親屬編概要",
    "0507": "資料處理概要",
}

# 高考三級 (114080) 的科目名稱 — 特定代碼在高考語境下的名稱
MOEX_114080_SUBJECT_NAMES = {
    "0101": "國文（作文與測驗）",
    "0102": "國文（作文與測驗）",
    "0301": "政治學",
    "0302": "政治學概要",
    "0303": "行政學",
    "0304": "行政學概要",
    "0305": "公共政策",
    "0307": "地方自治法規概要",
    "0401": "法學知識與英文",
    "0402": "法學知識與英文",
    "0403": "行政法",
    "0404": "公共管理",
    "0406": "行政法概要",
    "0506": "電子計算機概要",
    "0507": "資料處理概要",
}

# 考試代碼 → 考試名稱
EXAM_NAMES = {
    "112010": "112年初等考試",
    "112080": "112年高等考試三級考試暨普通考試",
    "113010": "113年初等考試",
    "113080": "113年高等考試三級考試暨普通考試",
    "114010": "114年初等考試",
    "114080": "114年高等考試三級考試暨普通考試",
}

# 初等考試類科代碼 → 名稱
ELEMENTARY_CATEGORY_NAMES = {
    "501": "一般行政", "502": "社會行政", "503": "人事行政",
    "504": "教育行政", "505": "財稅行政", "506": "統計",
    "507": "會計", "508": "經建行政", "509": "地政",
    "510": "圖書資訊管理", "511": "廉政", "512": "交通行政",
    "513": "電子工程", "514": "機械工程", "515": "土木工程",
    "516": "測量製圖",
}

# iPAS 科目名稱
IPAS_SUBJECT_NAMES = {
    "ai_planner": "AI 應用規劃師",
    "big_data": "巨量資料分析師",
    "information_security": "資訊安全工程師",
}

# 金融證照科目名稱
FINANCE_SUBJECT_NAMES = {
    "securities": "證券商業務員",
    "derivatives": "期貨商業務員",
    "anti_money_laundering": "防制洗錢與打擊資恐",
    "financial_planning": "理財規劃人員",
}


def compute_content_hash(questions: list) -> str:
    """計算題目內容的 hash，用於判斷是否重複"""
    content = json.dumps(
        [{"n": q.get("question_number"), "c": q.get("content", "")[:100]}
         for q in questions],
        ensure_ascii=False, sort_keys=True
    )
    return hashlib.md5(content.encode()).hexdigest()


def get_subject_name(exam_code: str, subject_code: str) -> str:
    """根據考試代碼和科目代碼取得科目名稱"""
    # 高普考使用特定對照表
    if exam_code.endswith("080"):
        name = MOEX_114080_SUBJECT_NAMES.get(subject_code)
        if name:
            return name
    # 通用對照表
    return MOEX_SUBJECT_NAMES.get(subject_code, f"科目 {subject_code}")


def get_exam_name(exam_code: str) -> str:
    """取得考試名稱"""
    return EXAM_NAMES.get(exam_code, f"考試 {exam_code}")


def scan_all_files(data_dir: Path) -> list:
    """掃描所有 JSON 檔案"""
    files = []
    for root, dirs, filenames in os.walk(data_dir):
        # 排除系統目錄
        dirs[:] = [d for d in dirs if not d.startswith("_")]
        for f in filenames:
            if not f.endswith(".json"):
                continue
            path = Path(root) / f
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                files.append({"path": path, "data": data})
            except Exception as e:
                print(f"  [ERROR] 無法讀取 {path}: {e}")
    return files


def classify_files(files: list) -> dict:
    """分類檔案為 MOEX / iPAS / Finance / Real Estate"""
    classified = {
        "moex": [],       # 考選部 (112xxx, 113xxx, 114xxx)
        "ipas": [],       # iPAS
        "finance": [],    # 金融證照
        "real_estate": [],  # 不動產
    }
    for f in files:
        rel = f["path"].relative_to(DATA_DIR)
        parts = rel.parts
        if parts[0] in ("ipas",):
            classified["ipas"].append(f)
        elif parts[0] in ("finance",):
            classified["finance"].append(f)
        elif parts[0] in ("real_estate",):
            classified["real_estate"].append(f)
        else:
            classified["moex"].append(f)
    return classified


def dedup_moex(moex_files: list, dry_run: bool) -> dict:
    """去重考選部資料：共用科目只保留一份"""
    # 按 exam_code 分組
    by_exam = defaultdict(list)
    for f in moex_files:
        rel = f["path"].relative_to(DATA_DIR)
        exam_code = rel.parts[0]  # e.g., "114080"
        by_exam[exam_code].append(f)

    stats = {"kept": 0, "removed": 0, "moved_to_shared": 0}

    for exam_code, exam_files in by_exam.items():
        # 按 subject_code 分組
        by_subject = defaultdict(list)
        for f in exam_files:
            rel = f["path"].relative_to(DATA_DIR)
            subject_code = rel.stem  # e.g., "0101"
            by_subject[subject_code].append(f)

        for subject_code, subject_files in by_subject.items():
            if len(subject_files) <= 1:
                # 唯一的，保留在原位
                stats["kept"] += 1
                continue

            # 驗證內容是否相同
            hashes = {}
            for sf in subject_files:
                qs = sf["data"].get("questions", [])
                h = compute_content_hash(qs)
                hashes[str(sf["path"])] = h

            unique_hashes = set(hashes.values())
            if len(unique_hashes) == 1:
                # 所有副本內容相同 → 共用科目，只保留一份
                keep = subject_files[0]
                shared_dir = DATA_DIR / exam_code / "_shared"
                shared_path = shared_dir / f"{subject_code}.json"

                if not dry_run:
                    shared_dir.mkdir(parents=True, exist_ok=True)

                # 更新 metadata 後移到 _shared
                keep_data = keep["data"]
                meta = keep_data.get("import_meta", {})
                meta["exam_code"] = exam_code
                meta["exam_name"] = get_exam_name(exam_code)
                meta["subject_code"] = subject_code
                meta["subject_name"] = get_subject_name(exam_code, subject_code)
                meta["category_code"] = "_shared"
                meta["category_name"] = "共用科目"
                meta["source"] = "考選部考畢試題查詢平臺"
                keep_data["import_meta"] = meta

                print(f"  [SHARED] {exam_code}/{subject_code} "
                      f"({get_subject_name(exam_code, subject_code)}) "
                      f"— 保留 1 份，移除 {len(subject_files)-1} 個重複")

                if not dry_run:
                    with open(shared_path, "w", encoding="utf-8") as fh:
                        json.dump(keep_data, fh, ensure_ascii=False, indent=2)

                    # 刪除所有原始副本
                    for sf in subject_files:
                        sf["path"].unlink(missing_ok=True)

                stats["moved_to_shared"] += 1
                stats["removed"] += len(subject_files) - 1
            else:
                # 內容不同 — 保留所有（可能是不同類科的專業科目）
                print(f"  [KEEP] {exam_code}/{subject_code} — "
                      f"{len(subject_files)} 個檔案，內容不同，全部保留")
                stats["kept"] += len(subject_files)

    return stats


def fix_metadata(data_dir: Path, dry_run: bool) -> int:
    """補全所有 JSON 檔案的 metadata"""
    fixed = 0
    for root, dirs, filenames in os.walk(data_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") or d == "_shared"]
        for f in filenames:
            if not f.endswith(".json"):
                continue
            path = Path(root) / f
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                continue

            meta = data.get("import_meta", {})
            changed = False
            rel = path.relative_to(data_dir)
            parts = rel.parts

            # MOEX 考選部
            if parts[0].isdigit() and len(parts[0]) == 6:
                exam_code = parts[0]
                subject_code = path.stem

                if not meta.get("exam_name") or meta["exam_name"] == "?":
                    meta["exam_name"] = get_exam_name(exam_code)
                    changed = True
                if not meta.get("subject_name") or meta["subject_name"] == "?":
                    meta["subject_name"] = get_subject_name(exam_code, subject_code)
                    changed = True
                if not meta.get("exam_code"):
                    meta["exam_code"] = exam_code
                    changed = True
                if not meta.get("subject_code"):
                    meta["subject_code"] = subject_code
                    changed = True
                if not meta.get("source"):
                    meta["source"] = "考選部考畢試題查詢平臺"
                    changed = True

                # 計算 year
                year_str = exam_code[:3]
                if year_str.isdigit():
                    meta["year"] = int(year_str)
                    changed = True

                # 類科名稱
                if len(parts) >= 2:
                    cat_code = parts[1]
                    if cat_code != "_shared":
                        cat_name = ELEMENTARY_CATEGORY_NAMES.get(cat_code)
                        if cat_name and meta.get("category_name") != cat_name:
                            meta["category_name"] = cat_name
                            changed = True

            # iPAS
            elif parts[0] == "ipas":
                if len(parts) >= 2:
                    subject_dir = parts[1]  # e.g., "ai_planner"
                    subject_name = IPAS_SUBJECT_NAMES.get(subject_dir, subject_dir)
                    if not meta.get("subject_name"):
                        meta["subject_name"] = subject_name
                        changed = True
                    if not meta.get("source"):
                        meta["source"] = "經濟部產業人才鑑定 (iPAS)"
                        changed = True

            # 金融證照
            elif parts[0] == "finance":
                if len(parts) >= 2:
                    subject_dir = parts[1]
                    subject_name = FINANCE_SUBJECT_NAMES.get(subject_dir, subject_dir)
                    if not meta.get("subject_name"):
                        meta["subject_name"] = subject_name
                        changed = True
                    if not meta.get("source"):
                        meta["source"] = "台灣金融研訓院"
                        changed = True

            # 不動產
            elif parts[0] == "real_estate":
                if not meta.get("source"):
                    meta["source"] = "內政部不動產資訊平台"
                    changed = True
                if not meta.get("subject_name"):
                    meta["subject_name"] = "不動產經紀人"
                    changed = True

            # 補全 questions_with_answer 和 total_questions
            qs = data.get("questions", [])
            with_answer = sum(1 for q in qs if q.get("correct_answer"))
            if meta.get("total_questions") != len(qs):
                meta["total_questions"] = len(qs)
                changed = True
            if meta.get("questions_with_answer") != with_answer:
                meta["questions_with_answer"] = with_answer
                changed = True

            if changed:
                data["import_meta"] = meta
                if not dry_run:
                    with open(path, "w", encoding="utf-8") as fh:
                        json.dump(data, fh, ensure_ascii=False, indent=2)
                fixed += 1

    return fixed


def remove_empty_files(data_dir: Path, dry_run: bool) -> list:
    """移除空檔案（0 題目）"""
    removed = []
    for root, dirs, filenames in os.walk(data_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") or d == "_shared"]
        for f in filenames:
            if not f.endswith(".json"):
                continue
            path = Path(root) / f
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                qs = data.get("questions", [])
                if len(qs) == 0:
                    print(f"  [EMPTY] {path.relative_to(data_dir)} — 移除")
                    if not dry_run:
                        path.unlink()
                    removed.append(str(path.relative_to(data_dir)))
            except Exception:
                continue
    return removed


def cleanup_empty_dirs(data_dir: Path, dry_run: bool) -> int:
    """清理空的目錄"""
    cleaned = 0
    for root, dirs, files in os.walk(data_dir, topdown=False):
        dirs[:] = [d for d in dirs if not d.startswith("_") or d == "_shared"]
        for d in dirs:
            dir_path = Path(root) / d
            if d.startswith("_") and d != "_shared":
                continue
            try:
                # 檢查是否為空目錄
                remaining = list(dir_path.iterdir())
                if not remaining:
                    print(f"  [RMDIR] {dir_path.relative_to(data_dir)}")
                    if not dry_run:
                        dir_path.rmdir()
                    cleaned += 1
            except Exception:
                continue
    return cleaned


def generate_report(data_dir: Path) -> dict:
    """生成清理後的報告"""
    report = {
        "total_files": 0,
        "total_questions": 0,
        "total_with_answers": 0,
        "by_exam": defaultdict(lambda: {"files": 0, "questions": 0, "with_answers": 0}),
        "no_answers": [],
    }

    for root, dirs, filenames in os.walk(data_dir):
        dirs[:] = [d for d in dirs if not d.startswith("_") or d == "_shared"]
        for f in filenames:
            if not f.endswith(".json"):
                continue
            path = Path(root) / f
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                continue

            meta = data.get("import_meta", {})
            qs = data.get("questions", [])
            with_answer = sum(1 for q in qs if q.get("correct_answer"))

            report["total_files"] += 1
            report["total_questions"] += len(qs)
            report["total_with_answers"] += with_answer

            exam_name = meta.get("exam_name", "未分類")
            report["by_exam"][exam_name]["files"] += 1
            report["by_exam"][exam_name]["questions"] += len(qs)
            report["by_exam"][exam_name]["with_answers"] += with_answer

            if len(qs) > 0 and with_answer == 0:
                report["no_answers"].append(str(path.relative_to(data_dir)))

    return report


def main():
    parser = argparse.ArgumentParser(description="考古題資料清理")
    parser.add_argument("--dry-run", action="store_true", help="預覽模式，不實際修改")
    args = parser.parse_args()

    dry_run = args.dry_run
    mode = "預覽模式" if dry_run else "執行模式"
    print(f"\n{'='*60}")
    print(f"考古題資料清理 — {mode}")
    print(f"{'='*60}")
    print(f"資料目錄: {DATA_DIR}")

    if not DATA_DIR.exists():
        print("ERROR: 資料目錄不存在")
        sys.exit(1)

    # Step 0: 備份
    if not dry_run and not BACKUP_DIR.exists():
        print(f"\n[Step 0] 備份原始資料到 {BACKUP_DIR.name}/")
        # 只備份 metadata（不複製整個目錄，太大）
        backup_meta = {}
        for root, dirs, filenames in os.walk(DATA_DIR):
            dirs[:] = [d for d in dirs if not d.startswith("_")]
            for f in filenames:
                if f.endswith(".json"):
                    path = Path(root) / f
                    rel = str(path.relative_to(DATA_DIR))
                    try:
                        with open(path) as fh:
                            data = json.load(fh)
                        backup_meta[rel] = data.get("import_meta", {})
                    except Exception:
                        pass
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        with open(BACKUP_DIR / "metadata_backup.json", "w", encoding="utf-8") as fh:
            json.dump(backup_meta, fh, ensure_ascii=False, indent=2)
        print(f"  已備份 {len(backup_meta)} 個檔案的 metadata")

    # Step 1: 移除空檔案
    print(f"\n[Step 1] 移除空檔案")
    removed = remove_empty_files(DATA_DIR, dry_run)
    print(f"  移除了 {len(removed)} 個空檔案")

    # Step 2: 去重考選部共用科目
    print(f"\n[Step 2] 去重考選部共用科目")
    all_files = scan_all_files(DATA_DIR)
    classified = classify_files(all_files)
    dedup_stats = dedup_moex(classified["moex"], dry_run)
    print(f"  保留: {dedup_stats['kept']}, "
          f"移至 _shared: {dedup_stats['moved_to_shared']}, "
          f"移除重複: {dedup_stats['removed']}")

    # Step 3: 清理空目錄
    print(f"\n[Step 3] 清理空目錄")
    cleaned_dirs = cleanup_empty_dirs(DATA_DIR, dry_run)
    print(f"  清理了 {cleaned_dirs} 個空目錄")

    # Step 4: 補全 metadata
    print(f"\n[Step 4] 補全 metadata (exam_name, subject_name)")
    fixed = fix_metadata(DATA_DIR, dry_run)
    print(f"  修正了 {fixed} 個檔案的 metadata")

    # Step 5: 生成報告
    print(f"\n[Step 5] 生成清理報告")
    report = generate_report(DATA_DIR)
    print(f"\n{'='*60}")
    print(f"清理後統計")
    print(f"{'='*60}")
    print(f"總檔案數: {report['total_files']}")
    print(f"總題目數: {report['total_questions']}")
    print(f"有答案的: {report['total_with_answers']}")
    print(f"無答案的: {report['total_questions'] - report['total_with_answers']}")
    print()

    print(f"{'考試名稱':<40} {'檔案':>5} {'題數':>6} {'有答案':>6}")
    print("-" * 60)
    for exam_name, data in sorted(report["by_exam"].items()):
        print(f"{exam_name:<40} {data['files']:>5} {data['questions']:>6} {data['with_answers']:>6}")

    if report["no_answers"]:
        print(f"\n⚠ 完全無答案的檔案 ({len(report['no_answers'])} 個):")
        for p in report["no_answers"]:
            print(f"  - {p}")

    if dry_run:
        print(f"\n{'='*60}")
        print("以上為預覽，實際清理請移除 --dry-run 參數")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
