#!/usr/bin/env python3
"""原型：用 Claude Code CLI（Haiku 4.5）直接從 PDF 產出結構化題目 JSON。

測試兩種格式：
- iPAS：單檔含題目+內嵌答案
- 普考（moex）：Q/S 兩個 PDF 分離

用法：
    python3 claude_json_prototype.py ipas
    python3 claude_json_prototype.py moex
    python3 claude_json_prototype.py both
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent.parent
MODEL = "claude-haiku-4-5"

IPAS_PDF = BACKEND / "data/historical_questions/ipas/ai_planner/114_ai_application_4th.pdf"
MOEX_Q = BACKEND / "data/historical_questions/_pdf/114080/401/Q_0102.pdf"
MOEX_S = BACKEND / "data/historical_questions/_pdf/114080/401/S_0102.pdf"

JSON_SCHEMA_HINT = """輸出格式必須是 JSON 陣列，每題一個 object：
[
  {
    "question_number": 1,
    "content": "題幹完整文字（不含選項）",
    "option_a": "選項 A 文字",
    "option_b": "選項 B 文字",
    "option_c": "選項 C 文字",
    "option_d": "選項 D 文字",
    "correct_answer": "A" 或 "B" 或 "C" 或 "D" 或 "" （若 PDF 內沒標答案則留空字串）,
    "source_snippet": "該題在原 PDF 的前 40 字原文，供抽查用"
  }
]"""

UNIFIED_PROMPT = """請使用 Read 工具讀取以下 PDF，逐題抽取成結構化 JSON。

""" + JSON_SCHEMA_HINT + """

重要規則：
1. **忠實抽取**：題幹、選項文字必須與 PDF 完全一致，不要改寫、翻譯、摘要
1a. **題幹必須完整保留**：
   - 若題目前方有「」或『』包住的閱讀原文、情境敘述、古文引述、長篇文字等，**整段完整納入 content 欄位**，不可只保留最後那句提問
   - content 欄位等於「學生看到試卷上該題需要閱讀的全部文字（除了 A/B/C/D 選項）」
   - 範例：若 PDF 是 `1 「長達 200 字的文章...」根據上文，何者正確？`，content 必須包含整段文章 + 「根據上文，何者正確？」，而不是只有提問句
   - 英文閱讀測驗、情境題、圖表說明文字同理，全部納入 content
2. **答案判斷**：
   - 若 PDF 題號旁邊、上方或下方有明確標示 A/B/C/D 字母（例如 `D 49.` 這種格式），填入 correct_answer
   - 若 PDF 本身沒有答案（例如純試題冊），correct_answer 填空字串 ""
   - 不要猜測、不要自己推理答案
3. **只處理單選題**：排除複選題、申論題、非選題
4. **題號**：使用 PDF 原題號（阿拉伯數字）
5. **選項**：PDF 原文可能是 ①②③④ 或 (A)(B)(C)(D) 等，一律對應到 option_a/b/c/d
6. **source_snippet**：該題題幹的前 40 字，不含選項
7. **輸出**：只輸出 JSON 陣列，不要 markdown code fence、不要任何說明文字

PDF 路徑：__PDF_PATH__"""

ANSWER_MAP_PROMPT = """請使用 Read 工具讀取以下答案 PDF，抽取題號→答案對照。

輸出格式（JSON object）：
{{"1": "A", "2": "B", "3": "C", ...}}

規則：
1. 複選題答案（如 ACE）只取第一個字母
2. 沒有答案的題號不要列出
3. 只輸出 JSON object，不要 markdown、不要說明

PDF 路徑：__PDF_PATH__"""


def run_claude(prompt: str, timeout: int = 600) -> str:
    cmd = [
        "claude", "-p", prompt,
        "--model", MODEL,
        "--allowedTools", "Read",
        "--output-format", "text",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude failed: {r.stderr[:300]}")
    return r.stdout.strip()


def strip_code_fence(s: str) -> str:
    """保險：去掉可能的 markdown code fence。"""
    s = s.strip()
    if s.startswith("```"):
        lines = s.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        s = "\n".join(lines).strip()
    return s


def extract_questions(pdf: Path) -> list:
    print(f"\n→ 抽取 {pdf.name}")
    t0 = time.time()
    raw = run_claude(UNIFIED_PROMPT.replace("__PDF_PATH__", str(pdf.resolve())))
    print(f"  耗時 {time.time()-t0:.1f}s，{len(raw)} chars")
    data = json.loads(strip_code_fence(raw))
    return data


def extract_answer_map(pdf: Path) -> dict:
    print(f"\n→ 抽取答案 {pdf.name}")
    t0 = time.time()
    raw = run_claude(ANSWER_MAP_PROMPT.replace("__PDF_PATH__", str(pdf.resolve())))
    print(f"  耗時 {time.time()-t0:.1f}s，{len(raw)} chars")
    return json.loads(strip_code_fence(raw))


def test_ipas():
    print("=" * 60)
    print("測試 1：iPAS AI 應用規劃師（單檔含內嵌答案）")
    print("=" * 60)
    qs = extract_questions(IPAS_PDF)
    with_ans = sum(1 for q in qs if q.get("correct_answer"))
    print(f"\n✓ 抽出 {len(qs)} 題，{with_ans} 題有答案")
    if qs:
        q = qs[0]
        print(f"\nQ1 預覽：")
        print(f"  題號：{q['question_number']}")
        print(f"  題幹：{q['content'][:60]}...")
        print(f"  A: {q['option_a'][:40]}")
        print(f"  D: {q['option_d'][:40]}")
        print(f"  答案：{q['correct_answer']}")
        print(f"  snippet：{q.get('source_snippet', '')[:40]}")
    # 對照原 JSON
    orig = json.load(open(BACKEND / "data/historical_questions/ipas/ai_planner/114_ai_application_4th.json"))
    orig_ans = {q['question_number']: q['correct_answer'] for q in orig['questions']}
    new_ans = {q['question_number']: q['correct_answer'] for q in qs}
    match = sum(1 for n, a in new_ans.items() if orig_ans.get(n) == a)
    print(f"\n答案對照原 JSON：{match}/{len(orig_ans)} 一致")
    # 列出不一致的
    diffs = [(n, orig_ans.get(n), new_ans.get(n)) for n in orig_ans if orig_ans.get(n) != new_ans.get(n)]
    if diffs[:5]:
        print(f"不一致前 5 題：{diffs[:5]}")
    Path("/tmp/ipas_proto.json").write_text(json.dumps(qs, ensure_ascii=False, indent=2))
    print(f"完整結果：/tmp/ipas_proto.json")


def test_moex():
    print("\n" + "=" * 60)
    print("測試 2：普考 114080/401/0102（Q/S 分離）")
    print("=" * 60)
    qs = extract_questions(MOEX_Q)
    print(f"  題目抽出：{len(qs)} 題")

    ans_map = extract_answer_map(MOEX_S)
    print(f"  答案抽出：{len(ans_map)} 題")

    # 合併
    for q in qs:
        key = str(q["question_number"])
        if key in ans_map:
            q["correct_answer"] = ans_map[key]
    with_ans = sum(1 for q in qs if q.get("correct_answer"))
    print(f"\n✓ 合併後 {len(qs)} 題，{with_ans} 題有答案")
    if qs:
        q = qs[0]
        print(f"\nQ1 預覽：")
        print(f"  題號：{q['question_number']}")
        print(f"  題幹：{q['content'][:60]}...")
        print(f"  A: {q['option_a'][:40]}")
        print(f"  答案：{q['correct_answer']}")

    # 對照原 JSON
    orig_path = BACKEND / "data/historical_questions/114080/401/0102.json"
    if orig_path.exists():
        orig = json.load(open(orig_path))
        orig_ans = {q['question_number']: q['correct_answer'] for q in orig['questions']}
        new_ans = {q['question_number']: q['correct_answer'] for q in qs}
        match = sum(1 for n, a in new_ans.items() if orig_ans.get(n) == a and a)
        print(f"\n答案對照原 JSON：{match}/{sum(1 for v in orig_ans.values() if v)} 一致")
    Path("/tmp/moex_proto.json").write_text(json.dumps(qs, ensure_ascii=False, indent=2))
    print(f"完整結果：/tmp/moex_proto.json")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    if mode in ("ipas", "both"):
        test_ipas()
    if mode in ("moex", "both"):
        test_moex()
