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
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
import urllib3
import yaml

urllib3.disable_warnings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
PDF_DIR = BASE_DIR / "data" / "historical_questions" / "_pdf"
OUTPUT_DIR = BASE_DIR / "data" / "historical_questions"

DOWNLOAD_URL = "https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx"

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


# ── 解析 ────────────────────────────────────────────────────────────────

def parse_mc_questions(text: str) -> List[Dict]:
    """
    從 PDF 文字解析選擇題
    支援考選部格式：
      1 題目內容
      ① 選項A (Unicode U+E18C, ❶)
      ② 選項B (Unicode U+E18D, ❷)
      ③ 選項C (Unicode U+E18E, ❸)
      ④ 選項D (Unicode U+E18F, ❹)
    或傳統格式：(A) 選項A / （A）選項A
    """
    questions = []
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Unicode 選項標記對應表
    unicode_to_letter = {
        '\ue18c': 'A',  # ①
        '\ue18d': 'B',  # ②
        '\ue18e': 'C',  # ③
        '\ue18f': 'D',  # ④
    }

    # 分割成題目塊（按題號開始分割）
    lines = text.split('\n')
    questions_blocks = []
    current_q_num = None
    current_block = []

    for line in lines:
        # 檢查是否是新題號行（數字+空格+內容）
        match = re.match(r'^(\d{1,3})\s+(.+)$', line)
        if match:
            if current_q_num is not None:
                questions_blocks.append((current_q_num, '\n'.join(current_block)))
            current_q_num = int(match.group(1))
            current_block = [match.group(2)]
        elif current_q_num is not None:
            current_block.append(line)

    # 不要遺漏最後一個題目
    if current_q_num is not None:
        questions_blocks.append((current_q_num, '\n'.join(current_block)))

    # 解析每個題目塊
    for q_num, q_block in questions_blocks:
        # 分離題幹與選項
        options = {}
        content_lines = []
        option_start_idx = -1

        block_lines = q_block.split('\n')
        for idx, line in enumerate(block_lines):
            # 檢查是否以 Unicode 選項標記開始
            if line and line[0] in unicode_to_letter:
                letter = unicode_to_letter[line[0]]
                opt_text = line[1:].strip()
                options[letter] = opt_text
                if option_start_idx == -1:
                    option_start_idx = idx
            # 檢查是否以傳統選項標記開始 (A) 或 （A）
            elif re.match(r'^[（(]\s*([A-Da-d])\s*[）)]', line):
                match = re.match(r'^[（(]\s*([A-Da-d])\s*[）)]\s*(.*)$', line)
                if match:
                    letter = match.group(1).upper()
                    opt_text = match.group(2).strip()
                    options[letter] = opt_text
                    if option_start_idx == -1:
                        option_start_idx = idx
            elif option_start_idx == -1:
                # 還沒開始選項，此行是題幹
                content_lines.append(line)

        content = ' '.join(content_lines).strip()

        if content and len(options) >= 2:
            questions.append({
                "question_number": q_num,
                "content": content.replace("\n", " ").strip(),
                "type": "single_choice",
                "option_a": options.get("A", ""),
                "option_b": options.get("B", ""),
                "option_c": options.get("C", ""),
                "option_d": options.get("D", ""),
                "correct_answer": "",
                "explanation": "",
                "bloom_category": None,
            })

    return questions


def parse_answer_key(text: str) -> Dict[int, str]:
    """從答案 PDF 文字解析標準答案（支持表格格式）"""
    answers = {}

    # 考選部答案格式：
    # 題號 第1題 第2題 第3題 ...
    # 答案 D A B C ...
    # 或單行格式：第1題 D 第2題 A ...

    # 方法1：表格格式 - 找出題號行和答案行
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if '題號' in line and i + 1 < len(lines):
            next_line = lines[i + 1]
            if '答案' in next_line:
                # 這是表格格式，題號在當前行，答案在下一行
                # 使用簡單的策略：匹配 "第\d+題" 和後續的答案
                question_pattern = re.compile(r'第(\d+)題')
                questions = [(int(m.group(1)), m.start()) for m in question_pattern.finditer(line)]

                # 從答案行提取答案（答案行中 "答案" 之後的所有字母）
                answer_start = next_line.find('答案')
                if answer_start != -1:
                    answer_text = next_line[answer_start + 2:].strip()
                    # 提取所有大寫字母（可能是單個答案或多個答案如 ACE）
                    answer_letters = re.findall(r'[A-Z]+', answer_text)

                    for idx, (q_num, _) in enumerate(questions):
                        if idx < len(answer_letters):
                            # 只取第一個字母（單選）或全部（複選）
                            ans = answer_letters[idx]
                            # 如果是複選題（多個字母），只取第一個用於 correct_answer
                            answers[q_num] = ans[0] if ans else ""

    # 方法2：如果表格格式解析失敗，嘗試單行格式
    if not answers:
        pattern = re.compile(r'第(\d+)題\s*([A-Z]+)')
        for match in pattern.finditer(text):
            q_num = int(match.group(1))
            ans = match.group(2).upper()
            answers[q_num] = ans[0] if ans else ""  # 只取第一個字母

    return answers


def cmd_parse():
    """解析已下載的 PDF 為 JSON"""
    try:
        import pdfplumber
    except ImportError:
        log.error("需要 pdfplumber：pip install pdfplumber")
        return

    if not PDF_DIR.exists():
        log.error(f"PDF 目錄不存在：{PDF_DIR}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parsed_count = 0

    for exam_code_dir in sorted(PDF_DIR.iterdir()):
        if not exam_code_dir.is_dir():
            continue

        for cat_code_dir in sorted(exam_code_dir.iterdir()):
            if not cat_code_dir.is_dir():
                continue

            exam_code = exam_code_dir.name
            cat_code = cat_code_dir.name

            q_files = sorted(cat_code_dir.glob("Q_*.pdf"))
            for q_file in q_files:
                sub_code = q_file.stem.replace("Q_", "")
                s_file = cat_code_dir / f"S_{sub_code}.pdf"

                if not s_file.exists():
                    log.warning(f"答案檔案遺失：{s_file}")
                    continue

                try:
                    log.info(f"解析：{exam_code}/{cat_code}/{sub_code}")

                    # 解析試題 PDF
                    with pdfplumber.open(q_file) as pdf:
                        q_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

                    questions = parse_mc_questions(q_text)

                    # 解析答案 PDF
                    with pdfplumber.open(s_file) as pdf:
                        s_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    answer_key = parse_answer_key(s_text)

                    # 合併答案
                    for q in questions:
                        q_num = q["question_number"]
                        if q_num in answer_key:
                            q["correct_answer"] = answer_key[q_num]

                    # 輸出 JSON
                    out_dir = OUTPUT_DIR / exam_code / cat_code
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"{sub_code}.json"

                    output = {
                        "import_meta": {
                            "source": "考選部考畢試題查詢平臺",
                            "exam_code": exam_code,
                            "category_code": cat_code,
                            "subject_code": sub_code,
                            "total_questions": len(questions),
                            "questions_with_answer": sum(1 for q in questions if q["correct_answer"]),
                        },
                        "questions": questions,
                    }

                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(output, f, ensure_ascii=False, indent=2)

                    parsed_count += 1
                    log.info(f"  ✓ {len(questions)} 題，{len([q for q in questions if q['correct_answer']])} 題有答案")

                except Exception as e:
                    log.error(f"解析失敗 {q_file}: {e}", exc_info=True)

    log.info(f"\n解析完成：{parsed_count} 份")
    log.info(f"JSON 輸出位置：{OUTPUT_DIR}")


# ── 主程式 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="考選部高普考題庫爬蟲")
    parser.add_argument("command", choices=["download", "parse", "all"],
                        help="執行指令")
    parser.add_argument("--config", default="exam_catalog.yaml",
                        help="目錄配置檔（YAML）")
    args = parser.parse_args()

    # 支援相對路徑和絕對路徑
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent / args.config

    if not config_path.exists():
        log.error(f"設定檔不存在：{config_path}")
        sys.exit(1)

    if args.command == "download":
        cmd_download(str(config_path))
    elif args.command == "parse":
        cmd_parse()
    elif args.command == "all":
        cmd_download(str(config_path))
        cmd_parse()


if __name__ == "__main__":
    main()
