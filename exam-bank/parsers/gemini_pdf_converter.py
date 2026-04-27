"""
Gemini Flash PDF → Markdown 轉換器 v2.0

核心改進（相比 v1 Claude Sonnet 版）：
- 原生 PDF 上傳：Gemini 直接讀取 PDF，不經過 pdfplumber 文字提取
- 單次呼叫：整份 PDF 一次送入，不分批
- 速度：2-5 秒/份（v1: 15-30 秒）
- 成本：~$0.005/份（v1: ~$0.06）
- 4 層品質驗證閘門

用法:
    cd exam-bank/parsers
    python3 gemini_pdf_converter.py                     # 轉換所有未處理 PDF
    python3 gemini_pdf_converter.py --pdf path/to.pdf   # 轉換單一 PDF
    python3 gemini_pdf_converter.py --dry-run            # 只統計不轉換
    python3 gemini_pdf_converter.py --force              # 忽略 manifest 全部重轉
"""

import os
import re
import json
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import Optional
from collections import Counter
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ── 常數 ──

GEMINI_MODEL = "gemini-2.5-flash"
VALIDATION_MODEL = "gemini-2.5-flash"  # Layer 3 可改用不同 LLM
MAX_RETRIES = 2
REQUEST_DELAY_SEC = 1.0  # API 請求間延遲

# ── 7 種內容類型 ──

CONTENT_TYPES = ["exam", "regulation", "textbook", "summary", "formula", "syllabus", "general"]

# ── Stage 0：內容偵測 Prompt ──

DETECT_PROMPT = """分析這份文件的內容類型。必須歸類為以下 7 種之一：

1. **exam** — 考試試卷（有題號、選項、答案的考題）
2. **regulation** — 法規規範（法律條文、行政規則、金管會規定、考試相關法令）
3. **textbook** — 教材內容（教科書章節、參考書、有系統的知識講解）
4. **summary** — 重點整理（筆記、講義、考前衝刺、條列式重點）
5. **formula** — 公式表/計算（數學公式、財務公式、統計公式集）
6. **syllabus** — 考試大綱（官方考試範圍、簡章、考科主題與權重）
7. **general** — 一般文件（無法歸類到以上任何一種）

回傳 JSON（只回傳 JSON，不要其他文字）：

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

# ── 各內容類型的轉換 Prompt ──

CONVERT_PROMPTS = {
    "exam": """你是考題 PDF 結構化專家。這份 PDF 是考試試卷。

請將整份 PDF 轉換為結構化 Markdown 格式的考題列表。

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
   - 若 PDF 文件中明確印有答案（如答案表、行內標記「答：A」、或「正確答案：B」），才提取並標記
   - 若為 iPAS 格式（答案以 A/B/C/D 題號. 列出），從中提取
   - ⚠️ 若 PDF 中沒有明確印出答案，答案欄必須寫 **答案：待匹配**
   - ⚠️ 絕對禁止猜測或推理答案！你不是解題者，你是 PDF 結構化工具
   - ⚠️ 即使你認為知道正確答案，只要 PDF 原文沒有標示，就寫「待匹配」
5. 數學公式處理：
   - 行內公式用 KaTeX 語法 $...$ 包裹，例如 $P(A|B)$、$10^5$、$R^2$
   - 獨立公式用 $$...$$ 包裹
   - 上標用 ^，下標用 _，分數用 \\frac{}{}
   - 希臘字母用 \\alpha、\\beta、\\sigma 等
   - 根據 PDF 原始排版還原數學式，不要丟失任何數學符號
6. 程式碼片段用 `...` 包裹
7. 表格用 Markdown 表格語法
8. 只輸出 Markdown，不要任何說明文字、前言或結語""",

    "regulation": """你是法規文件結構化專家。這份文件包含法規、規範或行政規則。

請將整份文件轉換為結構化 Markdown。

規則：
1. 保留原始法規結構（編/章/節/條/項/款/目）
2. 每條法規格式：
   ## 第 N 條　條文標題（如有）
   條文內容完整保留，不省略任何文字。
   - 第一項：...
   - 第二項：...
3. 保留所有「但書」（但...不在此限）
4. 法律專有名詞保持原文，不改寫
5. 數字保留原始格式（中文數字或阿拉伯數字）
6. 表格用 Markdown 表格語法
7. 標記關鍵詞：罰則金額、期限、特殊條件用 **粗體**
8. 數學公式用 KaTeX：$...$ 行內，$$...$$ 獨立
9. 只輸出 Markdown，不要任何說明文字""",

    "textbook": """你是教材內容結構化專家。這份文件是教科書或參考書內容。

請將整份文件轉換為結構化 Markdown。

規則：
1. 保留原始章節結構：
   # 章標題
   ## 節標題
   ### 小節標題
2. 每個概念/定義用以下格式標記：
   > **定義：{術語名稱}**
   > 定義內容
3. 重要觀念用 **粗體** 標記
4. 範例用引用區塊標記：
   > **範例：**
   > 範例內容
5. 圖表描述保留為文字說明
6. 數學公式用 KaTeX：$...$ 行內，$$...$$ 獨立
7. 表格用 Markdown 表格語法
8. 保留所有腳注和參考來源
9. 只輸出 Markdown，不要任何說明文字""",

    "summary": """你是學習筆記整理專家。這份文件是重點整理、講義或筆記。

請將整份文件轉換為結構化 Markdown，適合製作閃卡（flashcard）複習。

規則：
1. 每個知識點用以下格式：
   ## 主題名稱
   - **重點 1**：說明
   - **重點 2**：說明
2. 條列式內容保持條列
3. 比較表格用 Markdown 表格
4. 口訣/記憶法用引用區塊：
   > 記憶法：...
5. 數學公式用 KaTeX：$...$ 行內，$$...$$ 獨立
6. 刪除明顯的個人塗鴉或無意義標記
7. 只輸出 Markdown，不要任何說明文字""",

    "formula": """你是數學公式整理專家。這份文件包含公式表或計算相關內容。

請將整份文件轉換為結構化 Markdown，所有公式必須用 KaTeX 格式。

規則：
1. 每個公式區塊格式：
   ## 公式名稱/用途
   $$公式$$
   - **變數說明**：
     - $x$ = 說明
     - $y$ = 說明
   - **使用情境**：何時使用此公式
2. 所有數學符號必須用 KaTeX：
   - 行內公式 $...$
   - 獨立公式 $$...$$
   - 分數 \\frac{a}{b}，根號 \\sqrt{x}
   - 上標 x^2，下標 x_i
   - 求和 \\sum，積分 \\int，極限 \\lim
   - 矩陣用 \\begin{pmatrix}...\\end{pmatrix}
3. 相關公式歸為同一章節
4. 表格用 Markdown 表格
5. 只輸出 Markdown，不要任何說明文字""",

    "syllabus": """你是考試大綱分析專家。這份文件是考試簡章、考科大綱或考試範圍說明。

請將整份文件轉換為結構化 Markdown。

規則：
1. 考科資訊格式：
   # 考試名稱
   ## 考科一：科目名稱
   - **考試範圍**：
     1. 主題一（佔比 XX%）
     2. 主題二（佔比 XX%）
   - **題型**：選擇題/問答題/混合
   - **題數**：N 題
   - **時間**：N 分鐘
   - **及格標準**：N 分
2. 保留所有百分比、權重、分數資訊
3. 考試日期、報名資訊用表格整理
4. 參考書目保留完整書名與版次
5. 只輸出 Markdown，不要任何說明文字""",

    "general": """你是文件結構化專家。請將這份文件轉換為乾淨的結構化 Markdown。

規則：
1. 保留原始文件結構（標題層級）
2. 移除頁首頁尾、浮水印、頁碼
3. 表格用 Markdown 表格語法
4. 數學公式用 KaTeX：$...$ 行內，$$...$$ 獨立
5. 圖片描述保留為文字說明
6. 只輸出 Markdown，不要任何說明文字""",
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


# ── Gemini API ──

def _get_client(api_key: str):
    from google import genai
    return genai.Client(api_key=api_key)


def _call_gemini_with_pdf(
    client, pdf_path: str, prompt: str,
    model: str = GEMINI_MODEL, thinking: bool = False,
) -> str:
    """原生 PDF 上傳 + LLM 處理（單次呼叫）

    Args:
        thinking: True=啟用思考模式（品質較高但慢 2x），False=直接輸出（轉換用）
    """

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    from google.genai import types

    config = types.GenerateContentConfig(
        temperature=0.1,
        max_output_tokens=65536,
        thinking_config=types.ThinkingConfig(thinking_budget=0) if not thinking else None,
    )

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                    types.Part.from_text(text=prompt),
                ],
            )
        ],
        config=config,
    )
    return response.text


# ── Stage 0：內容類型偵測 ──

def detect_content_type(client, pdf_path: str) -> dict:
    """偵測 PDF 內容類型（7 種：exam/regulation/textbook/summary/formula/syllabus/general）"""
    try:
        result_text = _call_gemini_with_pdf(client, pdf_path, DETECT_PROMPT)
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            result = json.loads(json_match.group())
            # 相容舊版 "type" 欄位
            if "type" in result and "content_type" not in result:
                old_type = result["type"]
                # 映射舊分類到新分類
                type_map = {"notes": "summary", "mixed": "general"}
                result["content_type"] = type_map.get(old_type, old_type)
            # 確保 content_type 是有效值
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


# ── MD → JSON 解析 ──

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


# ── 答案匹配（SFI 格式：從答案卷 PDF 匹配）──

def match_answers_from_pdf(client, questions: list, answer_pdf_path: str) -> list:
    """從答案卷 PDF 提取答案並匹配"""
    # 先嘗試用 Gemini 提取答案卷
    answer_prompt = """這是一份考試答案卷。請提取所有題號和對應答案。
只回傳 JSON 格式（不要其他文字）：
{"answers": {"1": "A", "2": "B", "3": "C", ...}}"""

    try:
        result_text = _call_gemini_with_pdf(client, answer_pdf_path, answer_prompt)
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            data = json.loads(json_match.group())
            answers = data.get("answers", {})

            for q in questions:
                num_str = str(q["question_number"])
                if (not q["correct_answer"] or q["correct_answer"] == "待匹配") and num_str in answers:
                    q["correct_answer"] = answers[num_str]

            return questions
    except Exception as e:
        logger.warning("Gemini 答案提取失敗，改用 regex: %s", str(e)[:80])

    # fallback: pdfplumber + regex
    try:
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
    except Exception as e:
        logger.warning("pdfplumber 答案提取也失敗: %s", str(e)[:80])

    return questions


# ── Layer 1：結構完整性驗證 ──

def validate_structure(questions: list, expected_count: int = 0) -> ValidationReport:
    """驗證轉換後的結構完整性"""
    errors = []
    warnings = []
    stats = {}

    if not questions:
        return ValidationReport("L1_structure", False, ["無任何題目"], [], {})

    # 題數檢查（Stage 0 的預估值僅供參考，容許較大範圍）
    actual = len(questions)
    stats["question_count"] = actual
    stats["expected_count"] = expected_count
    if expected_count > 0:
        ratio = actual / expected_count
        if ratio < 0.5:
            errors.append(f"題數嚴重不足：預期 ~{expected_count}，實際 {actual}（{ratio:.0%}）")
        elif ratio < 0.8:
            warnings.append(f"題數偏少：預期 ~{expected_count}，實際 {actual}（{ratio:.0%}）")
        elif ratio > 2.0:
            warnings.append(f"題數超出預期：預期 ~{expected_count}，實際 {actual}（{ratio:.0%}，可能為多科目合卷）")

    # 每題結構檢查
    incomplete = 0
    no_answer = 0
    short_stem = 0
    for q in questions:
        # 選項完整性
        opts = [q.get(f"option_{x}", "") for x in "abcd"]
        if not all(opts):
            incomplete += 1
            if incomplete <= 3:
                errors.append(f"題 {q['question_number']}：選項不完整")

        # 答案
        if q.get("correct_answer", "") not in ("A", "B", "C", "D"):
            no_answer += 1

        # 題幹長度
        if len(q.get("content", "")) < 10:
            short_stem += 1
            if short_stem <= 3:
                warnings.append(f"題 {q['question_number']}：題幹過短 ({len(q.get('content', ''))} 字)")

    stats["incomplete_options"] = incomplete
    stats["no_answer"] = no_answer
    stats["short_stem"] = short_stem

    # 答案分佈
    if questions:
        dist = Counter(q.get("correct_answer", "") for q in questions if q.get("correct_answer") in ("A", "B", "C", "D"))
        answered = sum(dist.values())
        stats["answer_distribution"] = dict(dist)
        stats["answer_rate"] = answered / len(questions) if questions else 0

        if answered > 10:
            for letter in "ABCD":
                ratio = dist.get(letter, 0) / answered
                if ratio > 0.45:
                    warnings.append(f"答案分佈異常：{letter} = {ratio:.0%}（預期 ~25%）")

    # 題幹引用完整性檢查 — 偵測引用外部內容但實際缺失的情況
    _REF_PATTERNS = [
        (re.compile(r'如(?:上|下)?圖|見圖|參考圖|圖\s*\d+|如附圖'), "圖片"),
        (re.compile(r'如下程式碼|下列程式碼|以下程式|下列程式|以下的程式|參考程式碼|如下所示的程式'), "程式碼"),
        (re.compile(r'如下表|下表|見表|參考表|表\s*\d+'), "表格"),
        (re.compile(r'如下圖表|以下圖表'), "圖表"),
    ]
    # 判斷實際內容是否包含程式碼或表格的特徵
    _CODE_INDICATORS = re.compile(r'```|def |class |import |print\(|for .* in |if .*:|function |var |const |let |SELECT |FROM ')
    _TABLE_INDICATORS = re.compile(r'\|.*\|.*\||┌|├|└|─{3,}')

    ref_missing = 0
    ref_details = []
    for q in questions:
        content = q.get("content", "")
        opts_text = " ".join(q.get(f"option_{x}", "") for x in "abcd")
        full_text = content + " " + opts_text

        for pattern, ref_type in _REF_PATTERNS:
            if pattern.search(content):
                # 檢查內容中是否真的有對應的內嵌資源
                has_resource = False
                if ref_type == "程式碼":
                    has_resource = bool(_CODE_INDICATORS.search(full_text))
                elif ref_type in ("表格", "圖表"):
                    has_resource = bool(_TABLE_INDICATORS.search(full_text))
                # 圖片在純文字轉換中幾乎都會缺失
                # ref_type == "圖片" → has_resource = False

                if not has_resource:
                    ref_missing += 1
                    if len(ref_details) < 5:
                        ref_details.append(f"題 {q['question_number']}：引用「{ref_type}」但內容缺失")
                    break  # 每題只報一次

    stats["ref_missing"] = ref_missing
    if ref_missing > 0:
        ref_pct = ref_missing / len(questions)
        for detail in ref_details:
            warnings.append(detail)
        if ref_missing > len(ref_details):
            warnings.append(f"...另有 {ref_missing - len(ref_details)} 題引用缺失")
        if ref_pct > 0.3:
            errors.append(f"引用完整性嚴重不足：{ref_missing}/{len(questions)} 題（{ref_pct:.0%}）引用外部內容但實際缺失")
        elif ref_pct > 0.1:
            warnings.append(f"引用完整性偏低：{ref_missing}/{len(questions)} 題（{ref_pct:.0%}）引用外部內容缺失")

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
        stats["missing_numbers"] = len(missing)

    passed = len(errors) == 0
    return ValidationReport("L1_structure", passed, errors, warnings, stats)


# ── Layer 2：答案交叉驗證 ──

def validate_answers_cross_check(questions: list, answer_pdf_answers: dict) -> ValidationReport:
    """[已棄用] 舊版 L2 驗證，請用 validate_answers_cross_check_v2"""
    return validate_answers_cross_check_v2(questions, answer_pdf_answers)


def validate_answers_cross_check_v2(
    questions: list,
    answer_pdf_answers: dict,
    llm_answers: Optional[dict] = None,
) -> ValidationReport:
    """L2 驗證 v2：答案覆蓋率檢查 + 參考性交叉比對

    核心邏輯（董事會 2026-04-03 批准）：
    - 答案卷 PDF 是唯一真實來源
    - L2 主要檢查：答案覆蓋率（答案卷能覆蓋多少題）
    - L2 次要檢查：LLM 幻覺答案 vs 答案卷的一致性（僅供參考，不影響 PASS/FAIL）

    Args:
        questions: 題目列表（含 correct_answer 欄位，已套用答案卷）
        answer_pdf_answers: {題號str: 答案str} — 從答案卷 PDF 提取
        llm_answers: {題號str: 答案str} — LLM 轉換時從題目 PDF 提取（可選，僅供參考）
    """
    errors = []
    warnings = []
    stats = {}

    total_questions = len(questions)
    if total_questions == 0:
        return ValidationReport("L2_answer_cross", True, [], ["無題目"], stats)

    # ── 主要指標：答案卷覆蓋率 ──
    answer_pdf_count = len({k for k, v in answer_pdf_answers.items()
                           if isinstance(v, str) and v in ("A", "B", "C", "D")}) if answer_pdf_answers else 0
    answered_in_questions = sum(1 for q in questions if q.get("correct_answer") in ("A", "B", "C", "D"))

    stats["total_questions"] = total_questions
    stats["answer_pdf_extracted"] = answer_pdf_count
    stats["questions_with_answer"] = answered_in_questions
    stats["questions_without_answer"] = total_questions - answered_in_questions

    if answer_pdf_count == 0:
        errors.append("答案卷提取失敗：0 題有答案")
        return ValidationReport("L2_answer_cross", False, errors, [], stats)

    coverage = answered_in_questions / total_questions
    stats["answer_coverage"] = f"{coverage:.1%}"

    if coverage < 0.5:
        errors.append(f"答案覆蓋率 {coverage:.0%} 過低（{answered_in_questions}/{total_questions}），超過半數題目無答案")
    elif coverage < 0.8:
        warnings.append(f"答案覆蓋率 {coverage:.0%}（{answered_in_questions}/{total_questions}），部分題目無答案將被排除")

    # ── 次要指標：LLM 幻覺答案 vs 答案卷（僅供參考，不影響 PASS/FAIL）──
    if llm_answers and answer_pdf_answers:
        cross_stats = {"compared": 0, "matched": 0, "mismatched": 0}
        for num_str, ref in answer_pdf_answers.items():
            llm_ans = llm_answers.get(num_str, "")
            if isinstance(llm_ans, str) and llm_ans in ("A", "B", "C", "D") and isinstance(ref, str) and ref in ("A", "B", "C", "D"):
                cross_stats["compared"] += 1
                if llm_ans == ref:
                    cross_stats["matched"] += 1
                else:
                    cross_stats["mismatched"] += 1

        if cross_stats["compared"] > 0:
            match_rate = cross_stats["matched"] / cross_stats["compared"]
            stats["llm_vs_answer_pdf"] = {
                "compared": cross_stats["compared"],
                "match_rate": f"{match_rate:.1%}",
                "note": "參考值：LLM 幻覺答案 vs 答案卷一致性（不影響 PASS/FAIL）",
            }
            if match_rate < 0.5:
                warnings.append(f"LLM 幻覺答案與答案卷一致率僅 {match_rate:.0%}（確認答案已改用答案卷來源）")

    passed = len(errors) == 0
    return ValidationReport("L2_answer_cross", passed, errors, warnings, stats)


# ── Layer 3：LLM 抽樣覆核（Cross-LLM）──

def validate_sampling(client, pdf_path: str, questions: list, sample_size: int = 3) -> ValidationReport:
    """隨機抽樣題目，用 LLM 對比原始 PDF 驗證正確性"""
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

    verify_prompt = f"""我從這份考試 PDF 提取了以下 {sample_size} 題。
請直接對照 PDF 原始內容，逐題檢查：
1. 題幹是否完整且與 PDF 原文一致？
2. 四個選項是否正確？
3. 答案標記是否正確？
4. 數學公式是否正確還原？

提取結果：
{sample_text}

回傳 JSON（只回傳 JSON）：
[{{"question_number": N, "match": true/false, "issues": "問題描述或空字串"}}]"""

    try:
        result_text = _call_gemini_with_pdf(client, pdf_path, verify_prompt, model=VALIDATION_MODEL)
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
                    issue_msg = f"題 {r.get('question_number')}: {r.get('issues', '未知問題')}"
                    if stats["issues"] <= 3:
                        warnings.append(issue_msg)

            if stats["issues"] > sample_size * 0.5:
                errors.append(f"抽樣 {sample_size} 題中 {stats['issues']} 題有問題，品質堪憂")

            passed = len(errors) == 0
            return ValidationReport("L3_sampling", passed, errors, warnings, stats)

    except Exception as e:
        logger.warning("Layer 3 抽樣覆核失敗: %s", str(e)[:100])

    return ValidationReport("L3_sampling", True, [], ["抽樣覆核執行失敗，跳過"], {"sampled": 0})


# ── Layer 4：統計異常偵測 ──

def validate_statistics(questions: list) -> ValidationReport:
    """基於歷史統計數據檢查異常"""
    warnings = []
    stats = {}

    if not questions:
        return ValidationReport("L4_statistics", True, [], ["無題目"], {})

    # 平均題幹長度
    avg_len = sum(len(q.get("content", "")) for q in questions) / len(questions)
    stats["avg_stem_length"] = round(avg_len, 1)
    if avg_len < 15:
        warnings.append(f"平均題幹長度 {avg_len:.0f} 字，偏短（正常 30-150）")
    elif avg_len > 300:
        warnings.append(f"平均題幹長度 {avg_len:.0f} 字，偏長（正常 30-150）")

    # 平均選項長度
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
            warnings.append(f"平均選項長度 {avg_opt:.0f} 字，過短（可能截斷）")

    # Bloom 分佈
    bloom_dist = Counter(q.get("bloom_category", "remember") for q in questions)
    stats["bloom_distribution"] = dict(bloom_dist)
    remember_ratio = bloom_dist.get("remember", 0) / len(questions)
    if remember_ratio > 0.95:
        warnings.append(f"Bloom remember 佔 {remember_ratio:.0%}，分佈過於集中")

    # 重複題幹偵測
    stems = [q.get("content", "")[:50] for q in questions]
    dup_count = len(stems) - len(set(stems))
    if dup_count > 0:
        warnings.append(f"發現 {dup_count} 題可能重複（前 50 字相同）")
        stats["duplicates"] = dup_count

    return ValidationReport("L4_statistics", True, [], warnings, stats)


# ── 主流程：單一 PDF 轉換 + 4 層驗證 ──

def convert_single_pdf(
    pdf_path: str,
    output_md_path: str,
    output_json_path: str,
    api_key: str,
    answer_pdf_path: Optional[str] = None,
    dry_run: bool = False,
    skip_validation: bool = False,
) -> dict:
    """將單一 PDF 轉換為 MD + JSON，並執行 4 層品質驗證"""

    client = _get_client(api_key)
    start_time = time.time()

    # Stage 0：內容類型偵測
    logger.info("  Stage 0: 內容類型偵測...")
    detection = detect_content_type(client, pdf_path)
    content_type = detection.get("content_type", "general")
    logger.info("    類型=%s, 預估題數=%s, 信心=%s, 依據=%s",
                content_type, detection.get("estimated_question_count"),
                detection.get("confidence"), detection.get("key_features", ""))

    expected_count = detection.get("estimated_question_count", 0)

    if dry_run:
        return {"status": "dry_run", "detection": detection}

    # 選擇對應 content_type 的 Prompt
    convert_prompt = CONVERT_PROMPTS.get(content_type, CONVERT_PROMPTS["general"])
    logger.info("  轉換中（Gemini Flash, type=%s）...", content_type)

    for retry in range(MAX_RETRIES + 1):
        try:
            full_md = _call_gemini_with_pdf(client, pdf_path, convert_prompt)
            break
        except Exception as e:
            if retry < MAX_RETRIES:
                logger.warning("  重試 %d: %s", retry + 1, str(e)[:80])
                time.sleep(3)
            else:
                logger.error("  轉換失敗: %s", str(e)[:100])
                return {"status": "error", "reason": str(e)[:200]}

    # 存 MD
    os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    # 解析 MD → JSON（僅 exam 類型需要結構化題目）
    questions = []
    answer_ref = {}
    answer_ref_for_l2 = {}
    llm_answers_for_l2 = {}

    if content_type == "exam":
        questions = parse_md_to_questions(full_md)
        logger.info("  解析出 %d 題", len(questions))

        # ── 答案處理策略（董事會 2026-04-03 批准，v4 修正）──
        # 優先順序：① 獨立答案卷 PDF → ② 題目 PDF 原文印刷答案 → ③ 排除
        # 「LLM 幻覺」= LLM 推理出的答案（PDF 原文沒有印）
        # 「原文印刷」= PDF 本身就有答案欄（如 iPAS 格式：答案印在表格左側）

        # Step A: 記錄 MD 解析出的答案 + 判斷是否為「原文印刷」
        md_extracted_answers = {
            str(q["question_number"]): q.get("correct_answer", "")
            for q in questions if q.get("correct_answer") in ("A", "B", "C", "D")
        }
        md_answer_count = len(md_extracted_answers)
        total_q = len(questions)

        # 判斷：若 MD 中 >80% 的題目都有答案，且答案來自 **答案：X** 格式
        # → 極大概率是 PDF 原文就印有答案（如 iPAS），不是 LLM 幻覺
        answers_are_printed = (
            total_q > 0
            and md_answer_count / total_q >= 0.8
            and bool(re.search(r'\*\*答案[：:]\s*[A-D]\*\*', full_md))
        )

        if answers_are_printed:
            logger.info("  PDF 原文印有答案: %d/%d 題（答案欄格式）", md_answer_count, total_q)
        else:
            logger.info("  LLM 從題目 PDF 提取到 %d 題答案（待驗證，可能為幻覺）", md_answer_count)

        # Step B: 清除答案 — 後續由可信來源重新填入
        for q in questions:
            q["correct_answer"] = ""
            q["answer_source"] = ""

        # Step C: 從可信來源填入答案
        # C-1: 優先使用獨立答案卷 PDF（最可信）
        if answer_pdf_path and os.path.exists(answer_pdf_path):
            logger.info("  匹配答案卷（最高優先）: %s", os.path.basename(answer_pdf_path))

            try:
                ans_text = _call_gemini_with_pdf(client, answer_pdf_path,
                    '提取所有題號和答案，回傳 JSON：{"answers": {"1": "A", "2": "B", ...}}')
                json_match = re.search(r'\{[\s\S]*\}', ans_text)
                if json_match:
                    answer_ref = json.loads(json_match.group()).get("answers", {})
                    for q in questions:
                        num_str = str(q["question_number"])
                        if num_str in answer_ref and isinstance(answer_ref[num_str], str) and answer_ref[num_str] in ("A", "B", "C", "D"):
                            q["correct_answer"] = answer_ref[num_str]
                            q["answer_source"] = "answer_pdf"
            except Exception as e:
                logger.warning("  Gemini 答案卷提取失敗，改用 pdfplumber: %s", str(e)[:80])
                try:
                    import pdfplumber
                    with pdfplumber.open(answer_pdf_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text() or ""
                            pairs = re.findall(r'(\d{1,3})\s+([A-D])', text)
                            for num_str, ans in pairs:
                                num = int(num_str)
                                if 1 <= num <= 200:
                                    answer_ref[str(num)] = ans
                    for q in questions:
                        num_str = str(q["question_number"])
                        if num_str in answer_ref and isinstance(answer_ref[num_str], str) and answer_ref[num_str] in ("A", "B", "C", "D"):
                            q["correct_answer"] = answer_ref[num_str]
                            q["answer_source"] = "answer_pdf_pdfplumber"
                except Exception as e2:
                    logger.warning("  pdfplumber 也失敗: %s", str(e2)[:80])

            time.sleep(REQUEST_DELAY_SEC)

        # C-2: 若無獨立答案卷，但 PDF 原文有印刷答案 → 使用原文答案
        elif answers_are_printed:
            logger.info("  使用 PDF 原文印刷答案（答案欄格式）")
            for q in questions:
                num_str = str(q["question_number"])
                if num_str in md_extracted_answers:
                    q["correct_answer"] = md_extracted_answers[num_str]
                    q["answer_source"] = "question_pdf_printed"
            answer_ref = md_extracted_answers

        # C-3: 都沒有 → 無法取得答案
        else:
            logger.warning("  ⚠️ 無答案來源（無答案卷、PDF 原文也無答案欄）— 題目將排除")

        # 統計答案覆蓋
        answered = sum(1 for q in questions if q["correct_answer"] in ("A", "B", "C", "D"))
        no_answer = len(questions) - answered
        logger.info("  答案覆蓋: %d/%d 題有答案（來自答案卷），%d 題無答案（將排除）",
                     answered, len(questions), no_answer)

        # L2 驗證用資料
        answer_ref_for_l2 = answer_ref
        llm_answers_for_l2 = llm_extracted_answers
    else:
        logger.info("  非考題類型 (%s)，MD 已儲存，跳過題目解析", content_type)

    # ── 4 層品質驗證 ──
    validations = []

    if not skip_validation:
        # Layer 1: 結構完整性
        logger.info("  Layer 1: 結構驗證...")
        v1 = validate_structure(questions, expected_count)
        validations.append(v1)
        logger.info("    %s — 錯誤:%d 警告:%d", "✅ PASS" if v1.passed else "❌ FAIL",
                     len(v1.errors), len(v1.warnings))

        # Layer 2: 答案覆蓋率 + 交叉參考
        logger.info("  Layer 2: 答案覆蓋率驗證...")
        v2 = validate_answers_cross_check_v2(
            questions, answer_ref_for_l2, llm_answers=llm_answers_for_l2
        )
        validations.append(v2)
        logger.info("    %s — 有答案:%s/%s 覆蓋率:%s",
                     "✅ PASS" if v2.passed else "❌ FAIL",
                     v2.stats.get("questions_with_answer"),
                     v2.stats.get("total_questions"),
                     v2.stats.get("answer_coverage", "N/A"))

        # Layer 3: LLM 抽樣覆核
        logger.info("  Layer 3: LLM 抽樣覆核...")
        time.sleep(REQUEST_DELAY_SEC)
        v3 = validate_sampling(client, pdf_path, questions)
        validations.append(v3)
        logger.info("    %s — 抽樣:%s 問題:%s",
                     "✅ PASS" if v3.passed else "❌ FAIL",
                     v3.stats.get("sampled"), v3.stats.get("issues"))

        # Layer 4: 統計異常
        logger.info("  Layer 4: 統計異常偵測...")
        v4 = validate_statistics(questions)
        validations.append(v4)
        logger.info("    %s — 警告:%d", "✅ PASS" if v4.passed else "❌ FAIL",
                     len(v4.warnings))

    # 判定最終品質
    all_passed = all(v.passed for v in validations) if validations else True
    quality_flag = "ok" if all_passed else "review"

    elapsed = time.time() - start_time

    # ── 無答案題目過濾（董事會 2026-04-03：無答案不列入考題）──
    all_questions = questions  # 保留完整列表供記錄
    valid_questions = [q for q in questions if q.get("correct_answer") in ("A", "B", "C", "D")]
    excluded_count = len(all_questions) - len(valid_questions)

    if excluded_count > 0:
        logger.info("  📋 過濾結果: %d 題有答案（列入題庫），%d 題無答案（已排除）",
                     len(valid_questions), excluded_count)

    # 統計
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
        "model": GEMINI_MODEL,
        "detection": detection,
    }

    # JSON 只存有答案的題目
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


# ── Manifest 管理 ──

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
    """SHA256 fingerprint（比 v1 的 size+mtime 更可靠）"""
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ── 批次轉換 ──

def batch_convert(base_dir: str, api_key: str, dry_run: bool = False, force: bool = False):
    """掃描所有 PDF 並轉換"""

    pdf_dir = os.path.join(base_dir, "..", "backend", "data", "historical_questions")
    md_dir = os.path.join(base_dir, "data", "markdown")
    json_dir = os.path.join(base_dir, "data", "json")
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

            # 找答案卷
            answer_pdf = None
            for apdf in answer_pdfs:
                # 嘗試多種命名慣例
                q_base = qpdf.replace("_questions.", "").replace("_q.", "").replace(".pdf", "")
                a_base = apdf.replace("_answers.", "").replace("_a.", "").replace(".pdf", "")
                if q_base == a_base or qpdf.replace("questions", "answers") == apdf or qpdf.replace("_q.", "_a.") == apdf:
                    answer_pdf = os.path.join(root, apdf)
                    break

            # Manifest 檢查
            current_fp = _pdf_fingerprint(pdf_path)
            prev = manifest.get(manifest_key, {})

            if not force and not dry_run and prev.get("status") == "ok":
                if prev.get("pdf_fingerprint") == current_fp and os.path.exists(md_path):
                    logger.info("  SKIP (已轉換，PDF 未變更): %s [%d 題, %s]",
                                qpdf, prev.get("questions", 0), prev.get("quality_flag", "?"))
                    skipped += 1
                    continue
                elif prev.get("pdf_fingerprint") != current_fp:
                    logger.info("  RE-CONVERT (PDF 已變更): %s", qpdf)

            logger.info("Converting: %s/%s%s", rel_dir, qpdf,
                         f" (答案卷: {os.path.basename(answer_pdf)})" if answer_pdf else "")

            result = convert_single_pdf(
                pdf_path, md_path, json_path, api_key,
                answer_pdf_path=answer_pdf,
                dry_run=dry_run,
            )

            total_pdfs += 1

            if result["status"] == "ok":
                total_questions += result["questions"]
                total_answers += result["with_answers"]
                flag = result.get("quality_flag", "?")
                logger.info("  ✅ %d 題 (%d 有答案) [%s] %.1f秒",
                            result["questions"], result["with_answers"],
                            flag, result["elapsed_seconds"])

                manifest[manifest_key] = {
                    "status": "ok",
                    "content_type": result.get("content_type", "exam"),
                    "pdf_fingerprint": current_fp,
                    "converted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "total_parsed": result.get("total_parsed", result["questions"]),
                    "questions": result["questions"],  # 有效題數（有答案）
                    "excluded_no_answer": result.get("excluded_no_answer", 0),
                    "with_answers": result["with_answers"],
                    "quality_flag": flag,
                    "elapsed_seconds": result["elapsed_seconds"],
                    "validation_summary": result.get("validation_summary", {}),
                    "md_path": md_path,
                    "json_path": json_path,
                    "llm_model": GEMINI_MODEL,
                    "converter": "gemini_pdf_converter_v3",  # v3: 答案卷唯一來源
                }
                _save_manifest(manifest_path, manifest)

            elif result["status"] == "dry_run":
                logger.info("  🔍 type=%s, est_questions=%s",
                            result.get("detection", {}).get("type"),
                            result.get("detection", {}).get("estimated_question_count"))
            else:
                failed += 1
                logger.warning("  ⚠️ %s: %s", result["status"], result.get("reason", ""))
                manifest[manifest_key] = {
                    "status": result["status"],
                    "pdf_fingerprint": current_fp,
                    "converted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "error": result.get("reason", "unknown"),
                    "converter": "gemini_pdf_converter_v2",
                }
                _save_manifest(manifest_path, manifest)

            # API rate limit 保護
            time.sleep(REQUEST_DELAY_SEC)

    logger.info("\n=== 完成 ===")
    logger.info("PDF: %d (skip: %d, fail: %d) | Questions: %d | Answers: %d",
                total_pdfs, skipped, failed, total_questions, total_answers)


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Flash PDF → MD 轉換器 v2")
    parser.add_argument("--pdf", help="轉換單一 PDF")
    parser.add_argument("--dry-run", action="store_true", help="只偵測不轉換")
    parser.add_argument("--force", action="store_true", help="忽略 manifest 強制重轉")
    parser.add_argument("--skip-validation", action="store_true", help="跳過 4 層驗證（加速）")
    args = parser.parse_args()

    # 讀取 API key
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "backend", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key and not args.dry_run:
        print("❌ GEMINI_API_KEY not set")
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
            skip_validation=args.skip_validation,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        batch_convert(base_dir, api_key, dry_run=args.dry_run, force=args.force)
