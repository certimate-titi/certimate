#!/usr/bin/env python3
"""
考選部高普考題庫爬蟲 (簡化版)

使用方式：
    # 下載 PDF
    python moex_simple.py download exam_catalog.yaml

    # 解析 PDF 為 JSON
    python moex_simple.py parse

    # 一次執行
    python moex_simple.py all exam_catalog.yaml
"""

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Optional

import requests
import urllib3
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_pdf_extract import (  # noqa: E402
    HAIKU,
    extract_subject,
)

urllib3.disable_warnings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR / "data" / "historical_questions" / "_pdf"
OUTPUT_DIR = BASE_DIR / "data" / "historical_questions"

DOWNLOAD_URL = "https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx"

CLAUDE_MODEL = HAIKU
EXTRACT_FAILED_LOG = "_failed.log"

session = requests.Session()
session.verify = False
session.headers.update({"User-Agent": "Mozilla/5.0"})


# ── 下載 ────────────────────────────────────────────────────────────────

def download_pdf(exam_code: str, cat_code: str, sub_code: str, file_type: str = "Q") -> Optional[bytes]:
    """下載單個 PDF"""
    params = {"t": file_type, "code": exam_code, "c": cat_code, "s": sub_code, "q": "1"}
    try:
        resp = session.get(DOWNLOAD_URL, params=params, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 300:
            return resp.content
    except Exception as e:
        log.warning(f"下載失敗 {exam_code}/{cat_code}/{sub_code}: {e}")
    return None


def cmd_download(catalog_file: str):
    """根據 YAML 目錄下載 PDF"""
    with open(catalog_file, "r", encoding="utf-8") as f:
        catalog = yaml.safe_load(f)

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    downloaded = 0

    for exam_code, categories in catalog.items():
        if not categories:  # skip None/empty entries
            continue

        log.info(f"\n{'='*60}")
        log.info(f"考試：{exam_code}")

        for cat_code, subjects in categories.items():
            cat_dir = PDF_DIR / exam_code / cat_code
            cat_dir.mkdir(parents=True, exist_ok=True)

            for sub_code in subjects:
                total += 1
                q_file = cat_dir / f"Q_{sub_code}.pdf"
                s_file = cat_dir / f"S_{sub_code}.pdf"

                # 檢查是否已存在
                if q_file.exists() and s_file.exists():
                    log.debug(f"  跳過 {cat_code}/{sub_code}（已存在）")
                    continue

                log.info(f"  下載 {cat_code}/{sub_code}...")

                # 下載試題
                if not q_file.exists():
                    q_data = download_pdf(exam_code, cat_code, sub_code, "Q")
                    if q_data:
                        q_file.write_bytes(q_data)
                        log.info(f"    ✓ 試題 ({len(q_data)} bytes)")
                    else:
                        log.warning(f"    ✗ 試題下載失敗")
                        continue

                # 下載答案
                if not s_file.exists():
                    s_data = download_pdf(exam_code, cat_code, sub_code, "S")
                    if s_data:
                        s_file.write_bytes(s_data)
                        log.info(f"    ✓ 答案 ({len(s_data)} bytes)")
                    else:
                        log.warning(f"    ✗ 答案下載失敗")

                downloaded += 1
                time.sleep(1)

    log.info(f"\n下載完成：{downloaded}/{total}")
    log.info(f"PDF 儲存位置：{PDF_DIR}")


# ── 解析（Claude JSON 抽取 + PyMuPDF 圖像配對） ────────────────────────

def parse_one_subject(exam_code: str, cat_code: str, sub_code: str,
                      q_file: Path, s_file: Path, out_file: Path,
                      run_review: bool = False) -> Dict:
    """解析單一科目（試題 + 答案 + figure）並寫入 JSON。回傳統計資訊。

    圖像存放於 out_file 同目錄下 figures/{sub_code}/，JSON 中 figure_urls 為相對路徑。
    """
    figures_dir = out_file.parent / "figures" / sub_code

    result = extract_subject(
        q_pdf=q_file,
        s_pdf=s_file,
        figures_dir=figures_dir,
        run_review=run_review,
    )
    questions = result["questions"]

    # 將絕對路徑轉為相對路徑（相對於 out_file 所在目錄），方便匯入 DB
    for q in questions:
        paths = q.pop("figure_paths", [])
        q["figure_urls"] = [
            str(Path(p).relative_to(out_file.parent)) for p in paths
        ]
        q.setdefault("type", "single_choice")
        q.setdefault("explanation", "")
        q.setdefault("bloom_category", None)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "import_meta": {
            "source": "考選部考畢試題查詢平臺",
            "exam_code": exam_code,
            "category_code": cat_code,
            "subject_code": sub_code,
            "total_questions": len(questions),
            "questions_with_answer": sum(1 for q in questions if q["correct_answer"]),
            "questions_with_figure": sum(1 for q in questions if q["figure_urls"]),
            "extractor": f"claude-cli/{CLAUDE_MODEL}",
        },
        "questions": questions,
    }
    if "review" in result:
        output["review"] = result["review"]

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return {
        "total": len(questions),
        "with_answer": sum(1 for q in questions if q["correct_answer"]),
        "with_figure": sum(1 for q in questions if q["figure_urls"]),
    }


def cmd_parse(workers: int = 4, force: bool = False, run_review: bool = False):
    """解析已下載的 PDF 為 JSON（使用 Claude Code CLI + Haiku 4.5）。

    - 預設 skip 已存在的 JSON（--force 可強制重跑）
    - 失敗寫入 OUTPUT_DIR/_failed.log
    """
    if not PDF_DIR.exists():
        log.error(f"PDF 目錄不存在：{PDF_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failed_log = OUTPUT_DIR / EXTRACT_FAILED_LOG

    tasks = []
    for exam_code_dir in sorted(PDF_DIR.iterdir()):
        if not exam_code_dir.is_dir():
            continue
        for cat_code_dir in sorted(exam_code_dir.iterdir()):
            if not cat_code_dir.is_dir():
                continue
            exam_code = exam_code_dir.name
            cat_code = cat_code_dir.name
            for q_file in sorted(cat_code_dir.glob("Q_*.pdf")):
                sub_code = q_file.stem.replace("Q_", "")
                s_file = cat_code_dir / f"S_{sub_code}.pdf"
                if not s_file.exists():
                    log.warning(f"答案檔案遺失：{s_file}")
                    continue

                out_file = OUTPUT_DIR / exam_code / cat_code / f"{sub_code}.json"
                if out_file.exists() and not force:
                    log.debug(f"跳過（已存在）：{out_file}")
                    continue

                tasks.append((exam_code, cat_code, sub_code, q_file, s_file, out_file, run_review))

    if not tasks:
        log.info("沒有待解析的 PDF")
        return

    log.info(f"待解析：{len(tasks)} 份，workers={workers}")
    parsed_count = 0
    failed_count = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {
            executor.submit(parse_one_subject, *task): task for task in tasks
        }
        for future in as_completed(future_to_task):
            exam_code, cat_code, sub_code, q_file, *_ = future_to_task[future]
            label = f"{exam_code}/{cat_code}/{sub_code}"
            try:
                stats = future.result()
                parsed_count += 1
                log.info(f"  ✓ {label} — {stats['total']} 題，答案 {stats['with_answer']}，含圖 {stats['with_figure']}")
            except Exception as e:
                failed_count += 1
                log.error(f"  ✗ {label}: {e}")
                with open(failed_log, "a", encoding="utf-8") as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{label}\t{q_file}\t{e}\n")

    log.info(f"\n解析完成：{parsed_count}/{len(tasks)}（失敗 {failed_count}）")
    if failed_count:
        log.info(f"失敗紀錄：{failed_log}")
    log.info(f"JSON 輸出位置：{OUTPUT_DIR}")


# ── 主程式 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="考選部高普考題庫爬蟲")
    parser.add_argument("command", choices=["download", "parse", "all"],
                        help="執行指令")
    parser.add_argument("--config", default="exam_catalog.yaml",
                        help="目錄配置檔（YAML）")
    parser.add_argument("--workers", type=int, default=4,
                        help="parse 並行數（預設 4）")
    parser.add_argument("--force", action="store_true",
                        help="parse 時強制重跑（忽略已存在的 JSON）")
    parser.add_argument("--review", action="store_true",
                        help="parse 時額外跑出題老師 reviewer（Sonnet，較慢但會標註品質問題）")
    args = parser.parse_args()

    if args.command in ("download", "all"):
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = Path(__file__).resolve().parent / args.config
        if not config_path.exists():
            log.error(f"設定檔不存在：{config_path}")
            sys.exit(1)

    if args.command == "download":
        cmd_download(str(config_path))
    elif args.command == "parse":
        cmd_parse(workers=args.workers, force=args.force, run_review=args.review)
    elif args.command == "all":
        cmd_download(str(config_path))
        cmd_parse(workers=args.workers, force=args.force, run_review=args.review)


if __name__ == "__main__":
    main()
