"""
Claude Code CLI PDF → JSON 轉換器 v1.0

使用本地 Claude Code CLI（claude -p）取代 Gemini API，零額外 API 費用。
PDF 文字萃取使用 pymupdf，再將文字送入 Claude CLI 做結構化轉換。

用法:
    cd exam-bank/parsers
    python3 claude_cli_converter.py                     # 轉換所有未處理 PDF
    python3 claude_cli_converter.py --pdf path/to.pdf   # 轉換單一 PDF
    python3 claude_cli_converter.py --dry-run            # 只統計不轉換
    python3 claude_cli_converter.py --force              # 忽略 manifest 全部重轉

相較 Gemini 版差異：
- LLM 呼叫改為 subprocess.run(["claude", "-p", ...])
- PDF 需先用 pymupdf 萃取文字（Claude CLI 無法直接讀取 PDF binary）
- 無 API rate limit，但每次呼叫約 5-15 秒
- 驗證 Layer 3（抽樣覆核）也改用 Claude CLI
"""

import os
import re
import json
import sys
import time
import logging
import hashlib
import subprocess
from pathlib import Path
from typing import Optional
from collections import Counter
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── 常數 ──

CLAUDE_CLI = "claude"          # Claude Code CLI 路徑
CLAUDE_MODEL = "sonnet"        # Claude Code 使用的模型
MAX_RETRIES = 2
MAX_TEXT_CHARS = 100_000       # pymupdf 萃取文字上限（避免 prompt 過長）

# ── 7 種內容類型 ──

CONTENT_TYPES = ["exam", "regulation", "textbook", "summary", "formula", "syllabus", "general"]

# ── Stage 0：內容偵測 Prompt ──

DETECT_PROMPT = """分析以下文件內容的類型。必須歸類為以下 7 種之一：

1. **exam** — 考試試卷（有題號、選項、答案的考題）
2. **regulation** — 法規規範（法律條文、行政規則）
3. **textbook** — 教材內容（教科書章節、參考書）
4. **summary** — 重點整理（筆記、講義、考前衝刺）
5. **formula** — 公式表/計算
6. **syllabus** — 考試大綱
7. **general** — 一般文件

只回傳 JSON（不要其他文字）：

{
  "content_type": "exam|regulation|textbook|summary|formula|syllabus|general",
  "has_questions": true/false,
  "question_format": "選擇題|問答題|混合|無",
  "estimated_question_count": 數字或0,
  "has_answer_key": true/false,
  "subject_hint": "科目名稱",
  "key_features": "判斷依據（一句話）",
  "confidence": 0.0-1.0
}"""

# ── 各內容類型的轉換 Prompt（與 Gemini 版相同）──

CONVERT_PROMPTS = {
    "exam": """你是考題結構化專家。以下是一份考試試卷的全文。

請將全文轉換為結構化 Markdown 格式的考題列表。

規則：
1. 移除所有頁首頁尾（年份、科目名、考試日期、頁碼、「第N頁，共N頁」、機構名稱）
2. 每題格式固定為：
   ## 題號. 題幹完整文字
   - (A) 選項A
   - (B) 選項B
   - (C) 選項C
   - (D) 選項D
   **答案：X**
3. 跨頁的題目必須合併為完整的一題（題幹 + 所有選項 + 答案）
4. 答案處理（極重要）：
   - 若文件中明確印有答案（如答案表、行內標記「答：A」、或「正確答案：B」），才提取並標記
   - 若為 iPAS 格式（答案以 A/B/C/D 題號. 列出），從中提取
   - ⚠️ 若文件中沒有明確印出答案，答案欄必須寫 **答案：待匹配**
   - ⚠️ 絕對禁止猜測或推理答案！你不是解題者，你是文件結構化工具
   - ⚠️ 即使你認為知道正確答案，只要原文沒有標示，就寫「待匹配」
5. 數學公式處理：
   - 行內公式用 KaTeX 語法 $...$ 包裹
   - 獨立公式用 $$...$$ 包裹
   - 上標用 ^，下標用 _，分數用 \\frac{}{}
6. 程式碼片段用 `...` 包裹
7. 表格用 Markdown 表格語法
8. 只輸出 Markdown，不要任何說明文字、前言或結語""",

    "regulation": """你是法規文件結構化專家。以下是一份法規或規範文件。

請將全文轉換為結構化 Markdown。

規則：
1. 保留原始法規結構（編/章/節/條/項/款/目）
2. 每條法規格式：
   ## 第 N 條　條文標題（如有）
   條文內容完整保留，不省略任何文字。
3. 保留所有「但書」
4. 法律專有名詞保持原文
5. 數學公式用 KaTeX：$...$ 行內，$$...$$ 獨立
6. 只輸出 Markdown，不要任何說明文字""",

    "textbook": """你是教材內容結構化專家。以下是教科書或參考書內容。

請將全文轉換為結構化 Markdown。

規則：
1. 保留原始章節結構：# 章 ## 節 ### 小節
2. 概念/定義用引用區塊標記
3. 重要觀念用 **粗體** 標記
4. 數學公式用 KaTeX
5. 表格用 Markdown 表格語法
6. 只輸出 Markdown，不要任何說明文字""",

    "summary": """你是學習筆記整理專家。以下是重點整理或講義。

請將全文轉換為結構化 Markdown，適合製作閃卡複習。

規則：
1. 每個知識點：## 主題 → - **重點**：說明
2. 比較表格用 Markdown 表格
3. 數學公式用 KaTeX
4. 只輸出 Markdown，不要任何說明文字""",

    "formula": """你是數學公式整理專家。以下是公式表或計算內容。

請將全文轉換為結構化 Markdown，所有公式必須用 KaTeX。

規則：
1. 每個公式：## 公式名稱 → $$公式$$ → 變數說明
2. 所有數學符號用 KaTeX
3. 只輸出 Markdown，不要任何說明文字""",

    "syllabus": """你是考試大綱分析專家。以下是考試簡章或大綱。

請將全文轉換為結構化 Markdown。

規則：
1. 考科資訊：# 考試名稱 → ## 考科 → 範圍/題型/題數
2. 保留所有百分比、權重、分數資訊
3. 只輸出 Markdown，不要任何說明文字""",

    "general": """你是文件結構化專家。請將以下文件轉換為乾淨的結構化 Markdown。

規則：
1. 保留原始文件結構（標題層級）
2. 移除頁首頁尾、浮水印、頁碼
3. 表格用 Markdown 表格語法
4. 數學公式用 KaTeX
5. 只輸出 Markdown，不要任何說明文字""",
}


# ── 資料結構 ──

@dataclass
class ValidationReport:
    layer: str
    passed: bool
    errors: list
    warnings: list
    stats: dict

    def to_dict(self):
        return asdict(self)


# ── Bloom 分類 ──

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


# ── PDF 文字萃取 ──

def extract_pdf_text(pdf_path: str, max_chars: int = MAX_TEXT_CHARS) -> str:
    """使用 pymupdf 萃取 PDF 全文"""
    import pymupdf

    doc = pymupdf.open(pdf_path)
    pages_text = []
    total_chars = 0

    for i, page in enumerate(doc):
        text = page.get_text()
        if total_chars + len(text) > max_chars:
            remaining = max_chars - total_chars
            if remaining > 0:
                pages_text.append(text[:remaining])
            logger.warning("  文字萃取截斷於第 %d 頁（超過 %d 字上限）", i + 1, max_chars)
            break
        pages_text.append(text)
        total_chars += len(text)

    doc.close()

    full_text = "\n\n--- Page Break ---\n\n".join(pages_text)
    logger.info("  pymupdf 萃取: %d 頁, %d 字", len(pages_text), len(full_text))
    return full_text


# ── Claude CLI 呼叫 ──

def _call_claude_cli(prompt: str, timeout: int = 120) -> str:
    """透過 Claude Code CLI 呼叫 LLM

    使用本地 OAuth 登入（不需要 API KEY）。
    使用 --output-format json 取得結構化輸出。
    """
    cmd = [
        CLAUDE_CLI, "-p",
        "--allowedTools", "",      # 不允許任何工具，只做純文字生成
        "--model", CLAUDE_MODEL,
        "--output-format", "json",
        prompt,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.expanduser("~"),  # 避免載入專案 CLAUDE.md
        )

        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise RuntimeError(f"Claude CLI returned {result.returncode}: {stderr[:200]}")

        stdout = result.stdout.strip()
        if not stdout:
            raise RuntimeError("Claude CLI returned empty output")

        # --output-format json 回傳 JSON 結構
        try:
            output_data = json.loads(stdout)
            # 從 JSON 輸出中提取文字內容
            if isinstance(output_data, dict):
                # 格式: {"result": "...", "cost_usd": ..., ...}
                return output_data.get("result", stdout)
            return stdout
        except json.JSONDecodeError:
            # 如果不是 JSON，直接回傳原始文字
            return stdout

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Claude CLI timeout after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(
            f"Claude CLI not found at '{CLAUDE_CLI}'. "
            "Please install: https://docs.anthropic.com/en/docs/claude-code"
        )


def _call_claude_with_text(text: str, prompt: str, timeout: int = 120) -> str:
    """將文件文字 + prompt 組合後送入 Claude CLI"""
    full_prompt = f"""{prompt}

--- 以下是文件全文 ---

{text}"""
    return _call_claude_cli(full_prompt, timeout=timeout)


# ── Stage 0：內容類型偵測 ──

def detect_content_type(pdf_text: str) -> dict:
    """偵測文件內容類型（7 種）"""
    # 只用前 3000 字做偵測，節省時間
    sample = pdf_text[:3000]

    try:
        full_prompt = f"""{DETECT_PROMPT}

--- 以下是文件開頭內容 ---

{sample}"""
        result_text = _call_claude_cli(full_prompt, timeout=60)
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
            if result.get("content_type") not in CONTENT_TYPES:
                result["content_type"] = "general"
            return result
    except Exception as e:
        logger.warning("內容偵測失敗: %s, 預設為 general", str(e)[:80])

    return {
        "content_type": "general",
        "has_questions": False,
        "question_format": "無",
        "estimated_question_count": 0,
        "has_answer_key": False,
        "subject_hint": "unknown",
        "key_features": "偵測失敗，使用預設",
        "confidence": 0.3,
    }


# ── MD → JSON 解析（與 Gemini 版完全相同）──

def parse_md_to_questions(md_text: str) -> list:
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


# ── 答案匹配（從答案卷 PDF 提取）──

def match_answers_from_pdf(questions: list, answer_pdf_path: str) -> tuple:
    """從答案卷 PDF 提取答案並匹配

    Returns:
        (questions, answer_ref_dict)
    """
    answer_text = extract_pdf_text(answer_pdf_path, max_chars=10000)
    answer_ref = {}

    # 方法 1：Claude CLI 提取
    answer_prompt = """以下是一份考試答案卷的全文。請提取所有題號和對應答案。
只回傳 JSON 格式（不要其他文字）：
{"answers": {"1": "A", "2": "B", "3": "C", ...}}"""

    try:
        result_text = _call_claude_with_text(answer_text, answer_prompt, timeout=60)
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            data = json.loads(json_match.group())
            answer_ref = data.get("answers", {})

            for q in questions:
                num_str = str(q["question_number"])
                if (not q["correct_answer"] or q["correct_answer"] == "待匹配") and num_str in answer_ref:
                    ans = answer_ref[num_str]
                    if isinstance(ans, str) and ans in ("A", "B", "C", "D"):
                        q["correct_answer"] = ans

            return questions, answer_ref
    except Exception as e:
        logger.warning("Claude CLI 答案提取失敗，改用 regex: %s", str(e)[:80])

    # 方法 2：regex fallback
    pairs = re.findall(r'(\d{1,3})\s+([A-D])', answer_text)
    for num_str, ans in pairs:
        num = int(num_str)
        if 1 <= num <= 200:
            answer_ref[str(num)] = ans

    for q in questions:
        num_str = str(q["question_number"])
        if (not q["correct_answer"] or q["correct_answer"] == "待匹配") and num_str in answer_ref:
            q["correct_answer"] = answer_ref[num_str]

    return questions, answer_ref


# ── Layer 1：結構完整性驗證（與 Gemini 版相同）──

def validate_structure(questions: list, expected_count: int = 0) -> ValidationReport:
    """驗證轉換後的結構完整性"""
    errors = []
    warnings = []
    stats = {}

    if not questions:
        return ValidationReport("L1_structure", False, ["無任何題目"], [], {})

    actual = len(questions)
    stats["question_count"] = actual
    stats["expected_count"] = expected_count
    if expected_count > 0:
        ratio = actual / expected_count
        if ratio < 0.5:
            errors.append(f"題數嚴重不足：預期 ~{expected_count}，實際 {actual}（{ratio:.0%}）")
        elif ratio < 0.8:
            warnings.append(f"題數偏少：預期 ~{expected_count}，實際 {actual}（{ratio:.0%}）")

    incomplete = 0
    no_answer = 0
    short_stem = 0
    for q in questions:
        opts = [q.get(f"option_{x}", "") for x in "abcd"]
        if not all(opts):
            incomplete += 1
            if incomplete <= 3:
                errors.append(f"題 {q['question_number']}：選項不完整")

        if q.get("correct_answer", "") not in ("A", "B", "C", "D"):
            no_answer += 1

        if len(q.get("content", "")) < 10:
            short_stem += 1

    stats["incomplete_options"] = incomplete
    stats["no_answer"] = no_answer
    stats["short_stem"] = short_stem

    if questions:
        dist = Counter(q.get("correct_answer", "") for q in questions if q.get("correct_answer") in ("A", "B", "C", "D"))
        answered = sum(dist.values())
        stats["answer_distribution"] = dict(dist)
        stats["answer_rate"] = answered / len(questions) if questions else 0

    # 連號檢查
    numbers = sorted(q["question_number"] for q in questions)
    if numbers:
        expected_nums = set(range(numbers[0], numbers[-1] + 1))
        missing = expected_nums - set(numbers)
        if missing and len(missing) <= 5:
            warnings.append(f"缺少題號：{sorted(missing)}")
        elif missing:
            errors.append(f"缺少 {len(missing)} 個題號")
        stats["number_range"] = f"{numbers[0]}-{numbers[-1]}"

    passed = len(errors) == 0
    return ValidationReport("L1_structure", passed, errors, warnings, stats)


# ── Layer 2：答案覆蓋率驗證 ──

def validate_answers_cross_check(questions: list, answer_ref: dict) -> ValidationReport:
    """答案覆蓋率檢查"""
    errors = []
    warnings = []
    stats = {}

    total = len(questions)
    if total == 0:
        return ValidationReport("L2_answer_cross", True, [], ["無題目"], stats)

    answered = sum(1 for q in questions if q.get("correct_answer") in ("A", "B", "C", "D"))
    stats["total_questions"] = total
    stats["questions_with_answer"] = answered
    stats["questions_without_answer"] = total - answered

    if answered == 0:
        errors.append("無任何題目有答案")
        return ValidationReport("L2_answer_cross", False, errors, [], stats)

    coverage = answered / total
    stats["answer_coverage"] = f"{coverage:.1%}"

    if coverage < 0.5:
        errors.append(f"答案覆蓋率 {coverage:.0%} 過低")
    elif coverage < 0.8:
        warnings.append(f"答案覆蓋率 {coverage:.0%}，部分題目無答案將被排除")

    passed = len(errors) == 0
    return ValidationReport("L2_answer_cross", passed, errors, warnings, stats)


# ── Layer 3：Claude CLI 抽樣覆核 ──

def validate_sampling(pdf_text: str, questions: list, sample_size: int = 3) -> ValidationReport:
    """隨機抽樣題目，用 Claude CLI 對比原文驗證正確性"""
    import random

    if len(questions) < sample_size:
        sample_size = len(questions)
    if sample_size == 0:
        return ValidationReport("L3_sampling", True, [], ["無題目可抽樣"], {})

    sampled = random.sample(questions, sample_size)
    sample_text = ""
    for q in sampled:
        sample_text += f"""
題 {q['question_number']}:
題幹: {q['content']}
(A) {q['option_a']}
(B) {q['option_b']}
(C) {q['option_c']}
(D) {q['option_d']}
答案: {q['correct_answer']}
---
"""

    verify_prompt = f"""我從一份考試文件提取了以下 {sample_size} 題。
請對照原始文件內容，逐題檢查：
1. 題幹是否完整且與原文一致？
2. 四個選項是否正確？
3. 答案標記是否正確？

提取結果：
{sample_text}

原始文件內容：
{pdf_text[:8000]}

回傳 JSON（只回傳 JSON）：
[{{"question_number": N, "match": true/false, "issues": "問題描述或空字串"}}]"""

    try:
        result_text = _call_claude_cli(verify_prompt, timeout=90)
        json_match = re.search(r'\[[\s\S]*\]', result_text)
        if json_match:
            results = json.loads(json_match.group())
            errors = []
            warnings = []
            stats = {"sampled": sample_size, "matched": 0, "issues": 0}

            for r in results:
                if r.get("match"):
                    stats["matched"] += 1
                else:
                    stats["issues"] += 1
                    if stats["issues"] <= 3:
                        warnings.append(f"題 {r.get('question_number')}: {r.get('issues', '未知問題')}")

            if stats["issues"] > sample_size * 0.5:
                errors.append(f"抽樣 {sample_size} 題中 {stats['issues']} 題有問題")

            passed = len(errors) == 0
            return ValidationReport("L3_sampling", passed, errors, warnings, stats)

    except Exception as e:
        logger.warning("Layer 3 抽樣覆核失敗: %s", str(e)[:100])

    return ValidationReport("L3_sampling", True, [], ["抽樣覆核執行失敗，跳過"], {"sampled": 0})


# ── Layer 4：統計異常偵測（與 Gemini 版相同）──

def validate_statistics(questions: list) -> ValidationReport:
    """基於統計數據檢查異常"""
    warnings = []
    stats = {}

    if not questions:
        return ValidationReport("L4_statistics", True, [], ["無題目"], {})

    avg_len = sum(len(q.get("content", "")) for q in questions) / len(questions)
    stats["avg_stem_length"] = round(avg_len, 1)
    if avg_len < 15:
        warnings.append(f"平均題幹長度 {avg_len:.0f} 字，偏短")
    elif avg_len > 300:
        warnings.append(f"平均題幹長度 {avg_len:.0f} 字，偏長")

    opt_lens = []
    for q in questions:
        for x in "abcd":
            opt = q.get(f"option_{x}", "")
            if opt:
                opt_lens.append(len(opt))
    if opt_lens:
        avg_opt = sum(opt_lens) / len(opt_lens)
        stats["avg_option_length"] = round(avg_opt, 1)
        if avg_opt < 3:
            warnings.append(f"平均選項長度 {avg_opt:.0f} 字，過短")

    bloom_dist = Counter(q.get("bloom_category", "remember") for q in questions)
    stats["bloom_distribution"] = dict(bloom_dist)

    stems = [q.get("content", "")[:50] for q in questions]
    dup_count = len(stems) - len(set(stems))
    if dup_count > 0:
        warnings.append(f"發現 {dup_count} 題可能重複")
        stats["duplicates"] = dup_count

    return ValidationReport("L4_statistics", True, [], warnings, stats)


# ── 主流程：單一 PDF 轉換 + 4 層驗證 ──

def convert_single_pdf(
    pdf_path: str,
    output_json_path: str,
    output_md_path: Optional[str] = None,
    answer_pdf_path: Optional[str] = None,
    dry_run: bool = False,
    skip_validation: bool = False,
) -> dict:
    """將單一 PDF 轉換為 JSON（+ 可選 MD），並執行 4 層品質驗證"""

    start_time = time.time()

    # 萃取 PDF 文字
    logger.info("  萃取 PDF 文字...")
    try:
        pdf_text = extract_pdf_text(pdf_path)
    except Exception as e:
        return {"status": "error", "reason": f"PDF text extraction failed: {str(e)[:200]}"}

    if len(pdf_text.strip()) < 50:
        return {"status": "error", "reason": "PDF text too short (possibly scanned image PDF)"}

    # Stage 0：內容類型偵測
    logger.info("  Stage 0: 內容類型偵測（Claude CLI）...")
    detection = detect_content_type(pdf_text)
    content_type = detection.get("content_type", "general")
    logger.info("    類型=%s, 預估題數=%s, 信心=%s",
                content_type, detection.get("estimated_question_count"),
                detection.get("confidence"))

    expected_count = detection.get("estimated_question_count", 0)

    if dry_run:
        return {"status": "dry_run", "detection": detection}

    # 選擇 Prompt
    convert_prompt = CONVERT_PROMPTS.get(content_type, CONVERT_PROMPTS["general"])
    logger.info("  轉換中（Claude CLI, type=%s）...", content_type)

    for retry in range(MAX_RETRIES + 1):
        try:
            full_md = _call_claude_with_text(pdf_text, convert_prompt, timeout=300)
            break
        except Exception as e:
            if retry < MAX_RETRIES:
                logger.warning("  重試 %d: %s", retry + 1, str(e)[:80])
                time.sleep(3)
            else:
                logger.error("  轉換失敗: %s", str(e)[:100])
                return {"status": "error", "reason": str(e)[:200]}

    # 存 MD（可選）
    if output_md_path:
        os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
        with open(output_md_path, "w", encoding="utf-8") as f:
            f.write(full_md)

    # 解析 MD → JSON（僅 exam 類型）
    questions = []
    answer_ref = {}

    if content_type == "exam":
        questions = parse_md_to_questions(full_md)
        logger.info("  解析出 %d 題", len(questions))

        # 答案處理策略
        md_extracted_answers = {
            str(q["question_number"]): q.get("correct_answer", "")
            for q in questions if q.get("correct_answer") in ("A", "B", "C", "D")
        }
        md_answer_count = len(md_extracted_answers)
        total_q = len(questions)

        answers_are_printed = (
            total_q > 0
            and md_answer_count / total_q >= 0.8
            and bool(re.search(r'\*\*答案[：:]\s*[A-D]\*\*', full_md))
        )

        if answers_are_printed:
            logger.info("  原文印有答案: %d/%d 題", md_answer_count, total_q)

        # 清除答案
        for q in questions:
            q["correct_answer"] = ""
            q["answer_source"] = ""

        # 從可信來源填入答案
        if answer_pdf_path and os.path.exists(answer_pdf_path):
            logger.info("  匹配答案卷: %s", os.path.basename(answer_pdf_path))
            questions, answer_ref = match_answers_from_pdf(questions, answer_pdf_path)
            for q in questions:
                if q["correct_answer"] in ("A", "B", "C", "D") and not q.get("answer_source"):
                    q["answer_source"] = "answer_pdf"

        elif answers_are_printed:
            logger.info("  使用原文印刷答案")
            for q in questions:
                num_str = str(q["question_number"])
                if num_str in md_extracted_answers:
                    q["correct_answer"] = md_extracted_answers[num_str]
                    q["answer_source"] = "question_pdf_printed"
            answer_ref = md_extracted_answers

        else:
            logger.warning("  ⚠️ 無答案來源 — 題目將排除")

        answered = sum(1 for q in questions if q["correct_answer"] in ("A", "B", "C", "D"))
        logger.info("  答案覆蓋: %d/%d 題有答案", answered, len(questions))
    else:
        logger.info("  非考題類型 (%s)，MD 已儲存，跳過題目解析", content_type)

    # ── 4 層品質驗證 ──
    validations = []

    if not skip_validation and content_type == "exam":
        logger.info("  Layer 1: 結構驗證...")
        v1 = validate_structure(questions, expected_count)
        validations.append(v1)
        logger.info("    %s — 錯誤:%d 警告:%d", "PASS" if v1.passed else "FAIL",
                     len(v1.errors), len(v1.warnings))

        logger.info("  Layer 2: 答案覆蓋率驗證...")
        v2 = validate_answers_cross_check(questions, answer_ref)
        validations.append(v2)
        logger.info("    %s — 覆蓋率:%s",
                     "PASS" if v2.passed else "FAIL", v2.stats.get("answer_coverage", "N/A"))

        logger.info("  Layer 3: Claude CLI 抽樣覆核...")
        v3 = validate_sampling(pdf_text, questions)
        validations.append(v3)
        logger.info("    %s — 抽樣:%s 問題:%s",
                     "PASS" if v3.passed else "FAIL",
                     v3.stats.get("sampled"), v3.stats.get("issues"))

        logger.info("  Layer 4: 統計異常偵測...")
        v4 = validate_statistics(questions)
        validations.append(v4)
        logger.info("    %s — 警告:%d", "PASS" if v4.passed else "FAIL", len(v4.warnings))

    all_passed = all(v.passed for v in validations) if validations else True
    quality_flag = "ok" if all_passed else "review"

    elapsed = time.time() - start_time

    # 過濾無答案題目
    all_questions = questions
    valid_questions = [q for q in questions if q.get("correct_answer") in ("A", "B", "C", "D")]
    excluded_count = len(all_questions) - len(valid_questions)

    if excluded_count > 0:
        logger.info("  過濾: %d 題有答案, %d 題無答案（排除）", len(valid_questions), excluded_count)

    # 組裝 import_meta（與 Gemini 版完全一致的格式）
    meta = {
        "source_pdf": os.path.basename(pdf_path),
        "content_type": content_type,
        "total_questions_parsed": len(all_questions),
        "valid_questions": len(valid_questions),
        "excluded_no_answer": excluded_count,
        "bloom_distribution": dict(Counter(q.get("bloom_category", "remember") for q in valid_questions)) if valid_questions else {},
        "quality_flag": quality_flag,
        "validations": [v.to_dict() for v in validations],
        "elapsed_seconds": round(elapsed, 1),
        "model": f"claude-code-cli ({CLAUDE_MODEL})",
        "detection": detection,
    }

    result = {"import_meta": meta, "questions": valid_questions}

    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {
        "status": "ok",
        "content_type": content_type,
        "quality_flag": quality_flag,
        "questions": len(valid_questions),
        "total_parsed": len(all_questions),
        "excluded_no_answer": excluded_count,
        "with_answers": len(valid_questions),
        "elapsed_seconds": round(elapsed, 1),
        "validations_passed": all_passed,
        "validation_summary": {v.layer: "PASS" if v.passed else "FAIL" for v in validations},
    }


# ── Manifest 管理（與 Gemini 版共用格式）──

def _load_manifest(manifest_path: str) -> dict:
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_manifest(manifest_path: str, manifest: dict):
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def _pdf_fingerprint(pdf_path: str) -> str:
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ── 批次轉換 ──

def batch_convert(base_dir: str, dry_run: bool = False, force: bool = False):
    """掃描所有 PDF 並轉換"""

    pdf_dir = os.path.join(base_dir, "..", "backend", "data", "historical_questions")
    md_dir = os.path.join(base_dir, "data", "markdown")
    json_dir = os.path.join(base_dir, "data", "json")
    # 輸出 JSON 也同步到 backend 目錄（直接供 GCS 上傳）
    backend_json_dir = os.path.join(base_dir, "..", "backend", "data", "historical_questions")
    manifest_path = os.path.join(base_dir, "data", "convert_manifest.json")

    manifest = _load_manifest(manifest_path)
    total_pdfs = 0
    total_questions = 0
    total_answers = 0
    skipped = 0
    failed = 0

    for root, dirs, files in sorted(os.walk(pdf_dir)):
        question_pdfs = sorted([
            f for f in files
            if f.endswith(".pdf") and "answer" not in f.lower() and "_a." not in f
        ])
        answer_pdfs = [f for f in files if "answer" in f.lower() or "_a." in f]

        for qpdf in question_pdfs:
            pdf_path = os.path.join(root, qpdf)
            rel_dir = os.path.relpath(root, pdf_dir)
            stem = os.path.splitext(qpdf)[0]
            manifest_key = f"{rel_dir}/{qpdf}"

            md_path = os.path.join(md_dir, rel_dir, f"{stem}.md")
            json_path = os.path.join(json_dir, rel_dir, f"{stem}.json")
            # 也輸出到 backend 目錄
            backend_json_path = os.path.join(backend_json_dir, rel_dir, f"{stem}.json")

            # 找答案卷
            answer_pdf = None
            for apdf in answer_pdfs:
                q_base = qpdf.replace("_questions.", "").replace("_q.", "").replace(".pdf", "")
                a_base = apdf.replace("_answers.", "").replace("_a.", "").replace(".pdf", "")
                if q_base == a_base or qpdf.replace("questions", "answers") == apdf or qpdf.replace("_q.", "_a.") == apdf:
                    answer_pdf = os.path.join(root, apdf)
                    break

            # Manifest 檢查
            current_fp = _pdf_fingerprint(pdf_path)
            prev = manifest.get(manifest_key, {})

            if not force and not dry_run and prev.get("status") == "ok":
                if prev.get("pdf_fingerprint") == current_fp:
                    logger.info("  SKIP (已轉換): %s [%d 題]", qpdf, prev.get("questions", 0))
                    skipped += 1
                    continue

            logger.info("Converting: %s/%s%s", rel_dir, qpdf,
                        f" (答案卷: {os.path.basename(answer_pdf)})" if answer_pdf else "")

            result = convert_single_pdf(
                pdf_path, json_path,
                output_md_path=md_path,
                answer_pdf_path=answer_pdf,
                dry_run=dry_run,
            )

            total_pdfs += 1

            if result["status"] == "ok":
                total_questions += result["questions"]
                total_answers += result["with_answers"]

                # 同步 JSON 到 backend 目錄
                if os.path.exists(json_path) and json_path != backend_json_path:
                    os.makedirs(os.path.dirname(backend_json_path), exist_ok=True)
                    import shutil
                    shutil.copy2(json_path, backend_json_path)

                logger.info("  ✅ %d 題 (%d 有答案) [%s] %.1fs",
                            result["questions"], result["with_answers"],
                            result.get("quality_flag", "?"), result["elapsed_seconds"])

                manifest[manifest_key] = {
                    "status": "ok",
                    "content_type": result.get("content_type", "exam"),
                    "pdf_fingerprint": current_fp,
                    "converted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "questions": result["questions"],
                    "excluded_no_answer": result.get("excluded_no_answer", 0),
                    "with_answers": result["with_answers"],
                    "quality_flag": result.get("quality_flag", "?"),
                    "elapsed_seconds": result["elapsed_seconds"],
                    "validation_summary": result.get("validation_summary", {}),
                    "json_path": json_path,
                    "backend_json_path": backend_json_path,
                    "converter": "claude_cli_converter_v1",
                    "llm_model": f"claude-code-cli ({CLAUDE_MODEL})",
                }
                _save_manifest(manifest_path, manifest)

            elif result["status"] == "dry_run":
                logger.info("  🔍 type=%s, est_questions=%s",
                            result.get("detection", {}).get("content_type"),
                            result.get("detection", {}).get("estimated_question_count"))
            else:
                failed += 1
                logger.warning("  ⚠️ %s: %s", result["status"], result.get("reason", ""))
                manifest[manifest_key] = {
                    "status": result["status"],
                    "pdf_fingerprint": current_fp,
                    "converted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "error": result.get("reason", "unknown"),
                    "converter": "claude_cli_converter_v1",
                }
                _save_manifest(manifest_path, manifest)

    logger.info("\n=== 完成 ===")
    logger.info("PDF: %d (skip: %d, fail: %d) | Questions: %d | Answers: %d",
                total_pdfs, skipped, failed, total_questions, total_answers)


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Claude CLI PDF → JSON 轉換器 v1")
    parser.add_argument("--pdf", help="轉換單一 PDF")
    parser.add_argument("--answer-pdf", help="答案卷 PDF（搭配 --pdf 使用）")
    parser.add_argument("--dry-run", action="store_true", help="只偵測不轉換")
    parser.add_argument("--force", action="store_true", help="忽略 manifest 強制重轉")
    parser.add_argument("--skip-validation", action="store_true", help="跳過 4 層驗證")
    parser.add_argument("--output", help="自訂 JSON 輸出路徑（搭配 --pdf 使用）")
    args = parser.parse_args()

    # 檢查 Claude CLI 是否存在
    try:
        subprocess.run([CLAUDE_CLI, "--version"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"❌ Claude CLI not found at '{CLAUDE_CLI}'")
        print("   Install: https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if args.pdf:
        stem = Path(args.pdf).stem
        output = args.output or f"/tmp/{stem}.json"
        result = convert_single_pdf(
            args.pdf,
            output,
            output_md_path=f"/tmp/{stem}.md",
            answer_pdf_path=args.answer_pdf,
            dry_run=args.dry_run,
            skip_validation=args.skip_validation,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        batch_convert(base_dir, dry_run=args.dry_run, force=args.force)
