"""
CertiMate 考古題 PDF 解析器
- 從 SFI / 考選部 / iPAS PDF 解析選擇題
- 自動匹配答案卷
- 輸出標準 JSON
"""
import pdfplumber
import re
import json
import os
import sys
from typing import Optional, List, Dict
from collections import Counter

# ── Bloom 分類關鍵字規則（啟發式） ──────────────────
BLOOM_RULES = [
    # (category, keywords/patterns, weight)
    ("remember", [
        r"下列何者(為|是|非|不是|正確|錯誤)",
        r"依.*規定",
        r"所謂.*係指",
        r"何者(不)?屬於",
        r"下列.*敘述.*何者",
        r"稱為",
        r"定義",
    ]),
    ("understand", [
        r"下列.*說明.*何者",
        r"意義",
        r"目的",
        r"原因",
        r"解釋",
        r"理由",
        r"概念",
        r"原理",
        r"差異",
        r"區別",
    ]),
    ("apply", [
        r"計算",
        r"求.*之值",
        r"應如何",
        r"若.*則",
        r"設.*求",
        r"某甲",
        r"某公司",
        r"案例",
        r"假設",
        r"情境",
        r"應繳",
        r"應付",
    ]),
    ("analyze", [
        r"比較",
        r"分析",
        r"關係",
        r"影響",
        r"因素",
        r"原因.*為何",
        r"差異.*為何",
        r"最.*主要",
        r"哪.*項.*正確",
    ]),
    ("evaluate", [
        r"最適當",
        r"最不適當",
        r"最佳",
        r"優先",
        r"評估",
        r"判斷",
        r"是否妥適",
        r"是否合理",
    ]),
    ("create", [
        r"規劃",
        r"設計",
        r"建議.*方案",
        r"提出",
        r"建構",
        r"策略",
    ]),
]

def classify_bloom(question_text: str) -> str:
    scores = Counter()
    for category, patterns in BLOOM_RULES:
        for pat in patterns:
            if re.search(pat, question_text):
                scores[category] += 1
    if not scores:
        return "remember"  # default
    return scores.most_common(1)[0][0]


# ── SFI 格式解析（標準選擇題） ──────────────────
def parse_sfi_questions(pdf_path: str) -> List[dict]:
    """解析 SFI 格式的 PDF 選擇題"""
    questions = []
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

    # 匹配題號 + 題目 + 選項
    # Pattern: 數字. 題目內容 (A)選項A (B)選項B (C)選項C (D)選項D
    # 需要處理跨行的情況

    # 先用題號分割
    parts = re.split(r'\n\s*(\d{1,3})\.\s*', full_text)
    # parts[0] = header, parts[1]=num, parts[2]=content, parts[3]=num, ...

    if len(parts) < 3:
        return questions

    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        raw = parts[i + 1].strip()

        q = extract_question_from_raw(num, raw)
        if q:
            questions.append(q)

    return questions


def extract_question_from_raw(num: int, raw: str) -> Optional[dict]:
    """從原始文字提取題目和選項"""
    # 嘗試多種選項格式
    # Format 1: (A)xxx (B)xxx (C)xxx (D)xxx
    opt_pattern = r'\(([A-D])\)\s*'

    # 找出所有選項位置
    matches = list(re.finditer(opt_pattern, raw))

    if len(matches) < 2:
        return None

    # 題幹 = 從開頭到第一個選項
    content = raw[:matches[0].start()].strip()
    content = re.sub(r'\s+', ' ', content)

    # 提取各選項
    options = {}
    for j, m in enumerate(matches):
        letter = m.group(1)
        start = m.end()
        end = matches[j + 1].start() if j + 1 < len(matches) else len(raw)
        opt_text = raw[start:end].strip()
        opt_text = re.sub(r'\s+', ' ', opt_text)
        options[letter] = opt_text

    if not content or len(options) < 2:
        return None

    return {
        "question_number": num,
        "content": content,
        "type": "single_choice",
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "correct_answer": "",
        "explanation": "",
        "bloom_category": classify_bloom(content),
    }


# ── 答案卷解析 ──────────────────
def parse_answer_sheet(pdf_path: str) -> Dict[int, str]:
    """解析答案卷，回傳 {題號: 答案} 映射"""
    answers = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            # 常見格式: "1 A 11 A 21 C 31 A 41 B"
            # 或: "1 A 2 B 3 C ..."
            # 找所有 (數字 字母) 配對
            pairs = re.findall(r'(\d{1,3})\s+([A-D](?:BCD|ACD|ABD|ABC|AB|AC|AD|BC|BD|CD|[A-D])*)', text)
            for num_str, ans in pairs:
                num = int(num_str)
                if 1 <= num <= 200:
                    answers[num] = ans[0] if len(ans) == 1 else ans
    return answers


# ── 考選部格式解析 ──────────────────
def parse_moex_questions(pdf_path: str) -> List[dict]:
    """解析考選部格式 — 選項無括號，4 選項一行或分行"""
    questions = []
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

    # 考選部格式: "3 題目內容\n 選項A 選項B 選項C 選項D"
    # 題號在行首，選項通常是 2-4 行，用空白分隔或換行
    # 有時也用 (A)(B)(C)(D)

    # 先嘗試 (A)(B)(C)(D) 格式
    test_q = parse_sfi_questions(pdf_path)
    if len(test_q) >= 5:
        return test_q

    # 考選部特殊格式: 題號開頭，選項用 ① ② ③ ④ 或直接列出
    # 分割題目: 行首數字 + 空格 + 文字
    parts = re.split(r'\n(\d{1,2})\s+', full_text)

    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        raw = parts[i + 1].strip()

        # 先試 (A)(B)(C)(D)
        q = extract_question_from_raw(num, raw)
        if q:
            questions.append(q)
            continue

        # 考選部格式：選項直接換行排列，每行一個選項
        lines = raw.split('\n')
        if len(lines) >= 2:
            # 最後幾行可能是選項（通常4個選項）
            # 找到選項開始的位置 — 通常是較短的行
            content_lines = []
            option_lines = []
            found_options = False

            # 嘗試找到選項模式: 行末或行首有 ① ② ③ ④
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # 若已經在選項區域
                if found_options:
                    option_lines.append(line)
                else:
                    content_lines.append(line)
                    # 如果行數夠多，最後幾行可能是選項
                    if len(content_lines) >= 2:
                        # 檢查剩餘行是否像選項（通常4行相似長度的文字）
                        remaining = [l.strip() for l in lines[len(content_lines):] if l.strip()]
                        if len(remaining) >= 3:
                            found_options = True

            if option_lines and len(option_lines) >= 3:
                content = ' '.join(content_lines)
                opt_map = {}
                for idx, opt in enumerate(option_lines[:4]):
                    letter = chr(65 + idx)  # A, B, C, D
                    opt_map[letter] = opt.strip()

                questions.append({
                    "question_number": num,
                    "content": re.sub(r'\s+', ' ', content),
                    "type": "single_choice",
                    "option_a": opt_map.get("A", ""),
                    "option_b": opt_map.get("B", ""),
                    "option_c": opt_map.get("C", ""),
                    "option_d": opt_map.get("D", ""),
                    "correct_answer": "",
                    "explanation": "",
                    "bloom_category": classify_bloom(content),
                })

    return questions


# ── iPAS 格式解析 ──────────────────
def parse_ipas_questions(pdf_path: str) -> List[dict]:
    """解析 iPAS 格式的 PDF

    iPAS 有兩種主要格式:
    1. 答案在前: "B 7. 題目內容 (A)xxx; (B)xxx; (C)xxx; (D)xxx"
    2. 標準格式: "7. 題目內容 (A)xxx (B)xxx (C)xxx (D)xxx"
    """
    questions = []
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"

    # 格式1: 答案在前 — "A/B/C/D 數字."
    # Pattern: 行首或空白後 [A-D] 數字.
    answer_first = re.findall(r'([A-D])\s+(\d{1,3})\.\s', full_text)

    if len(answer_first) >= 5:
        # 答案在前的格式
        answers_map = {int(num): ans for ans, num in answer_first}

        # 用 "字母 數字." 分割
        parts = re.split(r'[A-D]\s+(\d{1,3})\.\s*', full_text)

        for i in range(1, len(parts) - 1, 2):
            num = int(parts[i])
            raw = parts[i + 1].strip()

            q = extract_question_from_raw(num, raw)
            if not q:
                q = extract_question_semicolon_options(num, raw)
            if not q:
                q = extract_question_numbered_options(num, raw)

            if q:
                q["correct_answer"] = answers_map.get(num, "")
                questions.append(q)

        return questions

    # 格式2: 標準格式
    parts = re.split(r'\n\s*(\d{1,3})\.\s*', full_text)
    if len(parts) < 3:
        parts = re.split(r'(?:^|\n)\s*(\d{1,3})\s*[\.\、]\s*', full_text)

    if len(parts) < 3:
        return questions

    for i in range(1, len(parts) - 1, 2):
        num = int(parts[i])
        raw = parts[i + 1].strip()

        q = extract_question_from_raw(num, raw)
        if not q:
            q = extract_question_semicolon_options(num, raw)
        if not q:
            q = extract_question_numbered_options(num, raw)

        if q:
            questions.append(q)

    return questions


def extract_question_semicolon_options(num: int, raw: str) -> Optional[dict]:
    """處理分號分隔的 (A)xxx; (B)xxx; 格式"""
    # iPAS 經常用 (A)xxx；(B)xxx 分號或換行
    opt_pattern = r'\(([A-D])\)\s*'
    matches = list(re.finditer(opt_pattern, raw))

    if len(matches) < 2:
        return None

    content = raw[:matches[0].start()].strip()
    content = re.sub(r'\s+', ' ', content)
    # 移除結尾的分號
    content = content.rstrip('；;')

    options = {}
    for j, m in enumerate(matches):
        letter = m.group(1)
        start = m.end()
        end = matches[j + 1].start() if j + 1 < len(matches) else len(raw)
        opt_text = raw[start:end].strip()
        opt_text = re.sub(r'\s+', ' ', opt_text)
        opt_text = opt_text.rstrip('；;')
        options[letter] = opt_text

    if not content or len(options) < 2:
        return None

    return {
        "question_number": num,
        "content": content,
        "type": "single_choice",
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "correct_answer": "",
        "explanation": "",
        "bloom_category": classify_bloom(content),
    }


def extract_question_numbered_options(num: int, raw: str) -> Optional[dict]:
    """處理 (1)(2)(3)(4) 格式的選項"""
    opt_pattern = r'\((\d)\)\s*'
    matches = list(re.finditer(opt_pattern, raw))

    if len(matches) < 2:
        return None

    content = raw[:matches[0].start()].strip()
    content = re.sub(r'\s+', ' ', content)

    options = {}
    letter_map = {"1": "A", "2": "B", "3": "C", "4": "D"}
    for j, m in enumerate(matches):
        digit = m.group(1)
        letter = letter_map.get(digit, "")
        if not letter:
            continue
        start = m.end()
        end = matches[j + 1].start() if j + 1 < len(matches) else len(raw)
        opt_text = raw[start:end].strip()
        opt_text = re.sub(r'\s+', ' ', opt_text)
        options[letter] = opt_text

    if not content or len(options) < 2:
        return None

    return {
        "question_number": num,
        "content": content,
        "type": "single_choice",
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "correct_answer": "",
        "explanation": "",
        "bloom_category": classify_bloom(content),
    }


# ── 元資料提取 ──────────────────
def extract_metadata(pdf_path: str) -> dict:
    """從 PDF 第一頁提取考試年份、科目等元資料"""
    with pdfplumber.open(pdf_path) as pdf:
        text = (pdf.pages[0].extract_text() or "")[:500]

    meta = {"source_name": "", "year": 0, "session": 0, "subject": ""}

    # 年份
    m = re.search(r'(\d{2,3})\s*年', text)
    if m:
        meta["year"] = int(m.group(1))

    # 次數
    m = re.search(r'第\s*(\d+)\s*次', text)
    if m:
        meta["session"] = int(m.group(1))

    # 梯次 (iPAS)
    if meta["session"] == 0:
        m = re.search(r'第(\w+)梯次', text)
        if m:
            num_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
            meta["session"] = num_map.get(m.group(1), 0)

    # 第一行通常是考試名稱
    first_line = text.split('\n')[0].strip()
    meta["source_name"] = first_line

    # 科目
    m = re.search(r'(?:專業科目|科目)[：:]\s*(.+?)(?:\s*請填|$)', text)
    if m:
        meta["subject"] = m.group(1).strip()

    return meta


# ── 主流程：處理單個 PDF ──────────────────
def process_exam_pdf(question_pdf: str, answer_pdf: Optional[str] = None,
                     source_type: str = "sfi") -> dict:
    """處理一份考試 PDF，輸出標準 JSON 結構"""

    # 解析題目
    if source_type == "ipas":
        questions = parse_ipas_questions(question_pdf)
    elif source_type == "moex":
        questions = parse_moex_questions(question_pdf)
    else:
        questions = parse_sfi_questions(question_pdf)

    # 解析答案
    if answer_pdf and os.path.exists(answer_pdf):
        answers = parse_answer_sheet(answer_pdf)
        for q in questions:
            num = q["question_number"]
            if num in answers:
                q["correct_answer"] = answers[num]

    # 元資料
    meta = extract_metadata(question_pdf)

    # Bloom 分佈統計
    bloom_dist = Counter(q["bloom_category"] for q in questions)

    # 難度分佈（基於 Bloom：remember/understand=easy, apply=medium, analyze+=hard）
    difficulty_map = {
        "remember": "easy", "understand": "easy",
        "apply": "medium",
        "analyze": "hard", "evaluate": "hard", "create": "hard",
    }
    diff_dist = Counter(difficulty_map.get(q["bloom_category"], "medium") for q in questions)

    return {
        "import_meta": {
            "source_name": meta["source_name"],
            "subject": meta["subject"],
            "year": meta["year"],
            "session": meta["session"],
            "total_questions": len(questions),
            "bloom_distribution": dict(bloom_dist),
            "difficulty_distribution": dict(diff_dist),
            "source_pdf": os.path.basename(question_pdf),
            "answer_pdf": os.path.basename(answer_pdf) if answer_pdf else None,
        },
        "questions": questions,
    }


# ── 批次處理 ──────────────────
def batch_process(base_dir: str):
    """掃描所有目錄，自動配對 questions/answers PDF 並解析"""
    results = []

    for root, dirs, files in sorted(os.walk(base_dir)):
        pdfs = sorted([f for f in files if f.endswith(".pdf")])
        if not pdfs:
            continue

        # 分類：題目 vs 答案
        question_pdfs = [f for f in pdfs if "answer" not in f and "_a." not in f]
        answer_pdfs = [f for f in pdfs if "answer" in f or "_a." in f]

        # 判斷來源類型
        rel = os.path.relpath(root, base_dir)
        if "ipas" in rel:
            source_type = "ipas"
        elif "real_estate" in rel:
            source_type = "moex"
        else:
            source_type = "sfi"

        for qpdf in question_pdfs:
            qpath = os.path.join(root, qpdf)

            # 嘗試找配對的答案檔
            apath = None
            # SFI 命名: xxx_questions.pdf -> xxx_answers.pdf
            candidate = qpdf.replace("_questions.", "_answers.")
            if candidate in answer_pdfs:
                apath = os.path.join(root, candidate)
            # 考選部: xxx_q.pdf -> xxx_a.pdf
            candidate = qpdf.replace("_q.", "_a.")
            if candidate in answer_pdfs:
                apath = os.path.join(root, candidate)

            try:
                result = process_exam_pdf(qpath, apath, source_type)
                total = result["import_meta"]["total_questions"]
                answered = sum(1 for q in result["questions"] if q["correct_answer"])

                # 輸出 JSON
                json_name = os.path.splitext(qpdf)[0] + ".json"
                json_path = os.path.join(root, json_name)
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(result, jf, ensure_ascii=False, indent=2)

                bloom = result["import_meta"]["bloom_distribution"]
                status = "✅" if total >= 10 else "⚠️"
                print(f"  {status} {total:>3} 題 | {answered:>3} 有答 | {json_name:<60} | bloom: {bloom}")
                results.append(result)
            except Exception as e:
                print(f"  ❌ ERROR | {qpdf}: {e}")

    return results


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    print("=== CertiMate 考古題 PDF 批次解析 ===\n")
    all_results = batch_process(base)

    # 總計
    total_q = sum(r["import_meta"]["total_questions"] for r in all_results)
    total_answered = sum(
        sum(1 for q in r["questions"] if q["correct_answer"])
        for r in all_results
    )
    all_bloom = Counter()
    for r in all_results:
        all_bloom.update(r["import_meta"]["bloom_distribution"])

    print(f"\n{'='*60}")
    print(f"總計: {len(all_results)} 份試卷 | {total_q} 題 | {total_answered} 有答案")
    print(f"Bloom 分佈: {dict(all_bloom)}")
