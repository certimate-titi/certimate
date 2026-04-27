"""
LLM PDF → Markdown 轉換器

核心原則：原始資料轉換正確 > 事後清洗
使用 LLM 將考試 PDF 轉為結構化 Markdown，解決跨頁截斷問題。

用法:
    cd exam-bank/parsers
    python llm_pdf_converter.py                    # 轉換所有 PDF
    python llm_pdf_converter.py --pdf path/to.pdf  # 轉換單一 PDF
    python llm_pdf_converter.py --dry-run           # 只統計不轉換
"""

import os
import re
import json
import sys
import time
import logging
from pathlib import Path
from typing import Optional
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── 常數 ──

PAGES_PER_BATCH = 5        # 每批送 LLM 的頁數
MAX_RETRIES = 2             # LLM 呼叫失敗重試次數
BATCH_DELAY_SEC = 1.5       # 批次間延遲（避免 rate limit）

SYSTEM_PROMPT = "你是考題 PDF 結構化專家。將原始 PDF 文字轉為乾淨的 Markdown 考題格式。"

USER_PROMPT_TEMPLATE = """以下是考試 PDF 的原始文字提取（包含頁首頁尾雜訊）。
請將它轉換為結構化 Markdown 格式的考題列表。

規則：
1. 移除所有頁首（年份、科目名、考試日期、「答案 題 目」、頁碼、「第N頁，共N頁」）
2. 每題格式固定為：
   ## 題號. 題幹完整文字
   - (A) 選項A
   - (B) 選項B
   - (C) 選項C
   - (D) 選項D
   **答案：X**
3. 跨頁的題目必須合併為完整的一題（題幹+4選項+答案）
4. 答案從文字中的「A/B/C/D 題號.」格式提取（iPAS 格式）
5. 若是 SFI 格式（無答案在文中），答案欄寫 **答案：待匹配**
6. 數學公式處理：
   - 行內公式用 KaTeX 語法 $...$ 包裹，例如 $P(A|B)$、$10^5$、$R^2$
   - 獨立公式用 $$...$$ 包裹
   - 上標用 ^，下標用 _，分數用 \\frac{{}}{{}}
   - 希臘字母用 \\alpha、\\beta、\\sigma 等
   - PDF 提取時常丟失上標（如「10 5」應還原為 $10^5$），請根據語意還原
   - 程式碼片段用 `...` 包裹
7. 只輸出 Markdown，不要說明文字

原始文字：
{raw_text}"""


# ── Bloom 分類（沿用舊版）──

BLOOM_RULES = [
    ("remember", [r"下列何者(為|是|非|不是|正確|錯誤)", r"依.*規定", r"所謂.*係指",
                  r"何者(不)?屬於", r"下列.*敘述.*何者", r"稱為", r"定義"]),
    ("understand", [r"下列.*說明.*何者", r"意義", r"目的", r"原因", r"解釋",
                    r"概念", r"差異", r"區別"]),
    ("apply", [r"計算", r"求.*之值", r"應如何", r"若.*則", r"某甲", r"某公司",
               r"案例", r"假設", r"情境", r"應繳"]),
    ("analyze", [r"比較", r"分析", r"關係", r"影響", r"因素", r"最.*主要"]),
    ("evaluate", [r"最適當", r"最不適當", r"最佳", r"優先", r"評估", r"判斷"]),
    ("create", [r"規劃", r"設計", r"建議.*方案", r"提出", r"策略"]),
]

def classify_bloom(text: str) -> str:
    scores = Counter()
    for cat, patterns in BLOOM_RULES:
        for pat in patterns:
            if re.search(pat, text):
                scores[cat] += 1
    return scores.most_common(1)[0][0] if scores else "remember"


# ── LLM 呼叫 ──

def _call_llm(raw_text: str, api_key: str) -> str:
    """呼叫 Anthropic Claude 進行 PDF → MD 轉換"""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(raw_text=raw_text),
        }],
    )
    return response.content[0].text


# ── PDF → 分批原始文字 ──

def extract_pages(pdf_path: str) -> list[str]:
    """用 pdfplumber 提取每頁原始文字"""
    import pdfplumber
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t and t.strip():
                pages.append(t)
    return pages


def batch_pages(pages: list[str], batch_size: int = PAGES_PER_BATCH) -> list[str]:
    """將頁面分批，每批 batch_size 頁"""
    batches = []
    for i in range(0, len(pages), batch_size):
        batch = pages[i:i + batch_size]
        combined = "\n\n".join(
            f"=== PAGE {i + j + 1} ===\n{text}"
            for j, text in enumerate(batch)
        )
        batches.append(combined)
    return batches


# ── MD → JSON 解析 ──

def parse_md_to_questions(md_text: str) -> list[dict]:
    """從結構化 Markdown 提取題目"""
    questions = []
    parts = re.split(r'## (\d+)\.\s*', md_text)

    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        raw = parts[i + 1].strip()

        # 提取答案
        answer_match = re.search(r'\*\*答案[：:]\s*([A-D])\*\*', raw)
        answer = answer_match.group(1) if answer_match else ""

        # 提取選項
        options = {}
        for letter in "ABCD":
            m = re.search(
                rf'- \({letter}\)\s*(.+?)(?=\n- \([A-D]\)|\n\*\*答案|\Z)',
                raw, re.DOTALL
            )
            if m:
                options[letter] = m.group(1).strip()

        # 題幹
        first_opt = re.search(r'\n- \(A\)', raw)
        content = raw[:first_opt.start()].strip() if first_opt else raw.split('\n')[0]

        # 清理
        if answer_match:
            content = content.replace(answer_match.group(0), "").strip()

        questions.append({
            "question_number": num,
            "content": content,
            "type": "single_choice",
            "option_a": options.get("A", ""),
            "option_b": options.get("B", ""),
            "option_c": options.get("C", ""),
            "option_d": options.get("D", ""),
            "correct_answer": answer,
            "explanation": "",
            "bloom_category": classify_bloom(content),
        })

    return questions


# ── 答案匹配（SFI 格式需要從答案卷匹配）──

def match_answers_from_pdf(questions: list[dict], answer_pdf_path: str) -> list[dict]:
    """從答案卷 PDF 匹配答案"""
    import pdfplumber
    answers = {}
    with pdfplumber.open(answer_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pairs = re.findall(r'(\d{1,3})\s+([A-D])', text)
            for num_str, ans in pairs:
                num = int(num_str)
                if 1 <= num <= 200:
                    answers[num] = ans

    for q in questions:
        if not q["correct_answer"] or q["correct_answer"] == "待匹配":
            q["correct_answer"] = answers.get(q["question_number"], "")

    return questions


# ── 主流程：單一 PDF 轉換 ──

def convert_single_pdf(
    pdf_path: str,
    output_md_path: str,
    output_json_path: str,
    api_key: str,
    answer_pdf_path: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """將單一 PDF 轉換為 MD + JSON"""

    pages = extract_pages(pdf_path)
    if not pages:
        return {"status": "skip", "reason": "no pages", "questions": 0}

    if dry_run:
        batches = batch_pages(pages)
        return {"status": "dry_run", "pages": len(pages), "batches": len(batches)}

    # 分批送 LLM
    batches = batch_pages(pages)
    all_md_parts = []

    for idx, batch_text in enumerate(batches):
        logger.info("  Batch %d/%d (%d chars)...", idx + 1, len(batches), len(batch_text))

        for retry in range(MAX_RETRIES + 1):
            try:
                md_part = _call_llm(batch_text, api_key)
                all_md_parts.append(md_part)
                break
            except Exception as e:
                if retry < MAX_RETRIES:
                    logger.warning("  Retry %d: %s", retry + 1, str(e)[:80])
                    time.sleep(3)
                else:
                    logger.error("  Failed after %d retries: %s", MAX_RETRIES, str(e)[:80])
                    all_md_parts.append(f"<!-- LLM ERROR: batch {idx+1} -->\n")

        if idx < len(batches) - 1:
            time.sleep(BATCH_DELAY_SEC)

    # 合併 MD
    full_md = "\n\n".join(all_md_parts)

    # 存 MD
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    # 解析 MD → JSON
    questions = parse_md_to_questions(full_md)

    # 匹配答案（SFI 格式）
    if answer_pdf_path and os.path.exists(answer_pdf_path):
        questions = match_answers_from_pdf(questions, answer_pdf_path)

    # 統計
    meta = {
        "source_pdf": os.path.basename(pdf_path),
        "total_questions": len(questions),
        "with_answers": sum(1 for q in questions if q["correct_answer"]),
        "bloom_distribution": dict(Counter(q["bloom_category"] for q in questions)),
    }

    result = {"import_meta": meta, "questions": questions}

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {
        "status": "ok",
        "pages": len(pages),
        "batches": len(batches),
        "questions": len(questions),
        "with_answers": meta["with_answers"],
    }


# ── 批次轉換 ──

def _load_manifest(manifest_path: str) -> dict:
    """載入轉換 manifest — 追蹤每份 PDF 的轉換狀態避免重複花費"""
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_manifest(manifest_path: str, manifest: dict):
    """儲存 manifest"""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _pdf_fingerprint(pdf_path: str) -> str:
    """產生 PDF 指紋（大小+修改時間）用於偵測原始檔變更"""
    stat = os.stat(pdf_path)
    return f"{stat.st_size}_{int(stat.st_mtime)}"


def batch_convert(base_dir: str, api_key: str, dry_run: bool = False, force: bool = False):
    """掃描所有 PDF 並轉換。

    使用 manifest.json 追蹤轉換狀態，避免重複上傳分析：
    - 已轉換且 PDF 未變更 → SKIP（不花費 LLM 成本）
    - PDF 檔案有變更（大小/修改時間不同）→ 重新轉換
    - --force 參數 → 忽略 manifest 全部重新轉換
    """

    pdf_dir = os.path.join(base_dir, "..", "backend", "data", "historical_questions")
    md_dir = os.path.join(base_dir, "data", "markdown")
    json_dir = os.path.join(base_dir, "data", "json")
    manifest_path = os.path.join(base_dir, "data", "convert_manifest.json")

    manifest = _load_manifest(manifest_path)
    total_pdfs = 0
    total_questions = 0
    total_answers = 0
    skipped = 0

    for root, dirs, files in sorted(os.walk(pdf_dir)):
        question_pdfs = sorted([
            f for f in files
            if f.endswith(".pdf") and "answer" not in f and "_a." not in f
        ])
        answer_pdfs = [f for f in files if "answer" in f or "_a." in f]

        for qpdf in question_pdfs:
            pdf_path = os.path.join(root, qpdf)
            rel_dir = os.path.relpath(root, pdf_dir)
            stem = os.path.splitext(qpdf)[0]
            manifest_key = f"{rel_dir}/{qpdf}"

            md_path = os.path.join(md_dir, rel_dir, f"{stem}.md")
            json_path = os.path.join(json_dir, rel_dir, f"{stem}.json")

            # 找答案卷
            answer_pdf = None
            candidate = qpdf.replace("_questions.", "_answers.")
            if candidate in answer_pdfs:
                answer_pdf = os.path.join(root, candidate)
            candidate2 = qpdf.replace("_q.", "_a.")
            if candidate2 in answer_pdfs:
                answer_pdf = os.path.join(root, candidate2)

            # ── Manifest 檢查：避免重複轉換 ──
            current_fp = _pdf_fingerprint(pdf_path)
            prev = manifest.get(manifest_key, {})

            if not force and not dry_run and prev.get("status") == "ok":
                if prev.get("pdf_fingerprint") == current_fp and os.path.exists(md_path):
                    logger.info("  SKIP (已轉換，PDF 未變更): %s [%d 題]", qpdf, prev.get("questions", 0))
                    skipped += 1
                    continue
                elif prev.get("pdf_fingerprint") != current_fp:
                    logger.info("  RE-CONVERT (PDF 已變更): %s", qpdf)

            logger.info("Converting: %s/%s", rel_dir, qpdf)
            result = convert_single_pdf(
                pdf_path, md_path, json_path, api_key,
                answer_pdf_path=answer_pdf,
                dry_run=dry_run,
            )

            total_pdfs += 1
            if result["status"] == "ok":
                total_questions += result["questions"]
                total_answers += result["with_answers"]
                logger.info("  ✅ %d 題 (%d 有答案)", result["questions"], result["with_answers"])

                # 記錄到 manifest
                manifest[manifest_key] = {
                    "status": "ok",
                    "pdf_fingerprint": current_fp,
                    "converted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "questions": result["questions"],
                    "with_answers": result["with_answers"],
                    "pages": result["pages"],
                    "batches": result["batches"],
                    "md_path": md_path,
                    "json_path": json_path,
                    "llm_model": "claude-sonnet-4-20250514",
                }
                _save_manifest(manifest_path, manifest)

            elif result["status"] == "dry_run":
                logger.info("  🔍 %d pages, %d batches", result["pages"], result["batches"])
            else:
                logger.warning("  ⚠️ %s: %s", result["status"], result.get("reason", ""))
                manifest[manifest_key] = {
                    "status": result["status"],
                    "pdf_fingerprint": current_fp,
                    "converted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "error": result.get("reason", "unknown"),
                }
                _save_manifest(manifest_path, manifest)

    logger.info("\n=== 完成 ===")
    logger.info("PDF: %d (skip: %d) | Questions: %d | Answers: %d", total_pdfs, skipped, total_questions, total_answers)


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LLM PDF → MD 轉換器")
    parser.add_argument("--pdf", help="轉換單一 PDF")
    parser.add_argument("--dry-run", action="store_true", help="只統計不轉換")
    parser.add_argument("--force", action="store_true", help="忽略 manifest 強制重新轉換（會產生額外 LLM 成本）")
    args = parser.parse_args()

    # 讀取 API key
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.strip().split("=", 1)[1]

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key and not args.dry_run:
        print("❌ ANTHROPIC_API_KEY not set")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if args.pdf:
        stem = Path(args.pdf).stem
        result = convert_single_pdf(
            args.pdf,
            f"/tmp/{stem}.md",
            f"/tmp/{stem}.json",
            api_key,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))
    else:
        batch_convert(base_dir, api_key, dry_run=args.dry_run, force=args.force)
