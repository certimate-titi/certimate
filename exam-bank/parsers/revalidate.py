"""
重新驗證已轉換的 PDF v2 — 答案卷為唯一真實來源，無答案題目排除

策略：
1. 重新解析 MD → 題目
2. 清除 LLM 幻覺答案，僅從答案卷 PDF 提取答案
3. 過濾無答案題目
4. 重跑 4 層驗證
5. 更新 JSON + Manifest

用法: python3 parsers/revalidate.py
"""

import os
import sys
import json
import time
import re
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "parsers"))

from gemini_pdf_converter import (
    _get_client, _call_gemini_with_pdf,
    parse_md_to_questions,
    validate_structure, validate_answers_cross_check_v2,
    validate_sampling, validate_statistics,
    REQUEST_DELAY_SEC, GEMINI_MODEL,
)

MANIFEST_PATH = os.path.join(BASE_DIR, "data", "convert_manifest.json")
PDF_BASE = os.path.join(BASE_DIR, "..", "backend", "data", "historical_questions")


def find_answer_pdf(question_pdf_path):
    d = os.path.dirname(question_pdf_path)
    qname = os.path.basename(question_pdf_path)
    for pattern in ["questions", "_q."]:
        replacement = "answers" if pattern == "questions" else "_a."
        apath = os.path.join(d, qname.replace(pattern, replacement))
        if os.path.exists(apath):
            return apath
    return None


def revalidate_all():
    # 載入 API key
    env_path = os.path.join(BASE_DIR, "..", "backend", ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            if line.startswith("GEMINI_API_KEY="):
                os.environ["GEMINI_API_KEY"] = line.strip().split("=", 1)[1]
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return

    client = _get_client(api_key)

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    total = len(manifest)
    results_summary = []

    print(f"\n{'='*70}")
    print(f"  重新驗證 {total} 份 PDF（v3：答案卷唯一來源 + 無答案排除）")
    print(f"{'='*70}\n")

    for i, (key, entry) in enumerate(manifest.items(), 1):
        if entry.get("status") != "ok":
            continue

        md_path = entry.get("md_path", "")
        json_path = entry.get("json_path", "")
        pdf_path = os.path.join(PDF_BASE, key)
        answer_pdf = find_answer_pdf(pdf_path)

        print(f"\n[{i}/{total}] {key}")

        if not os.path.exists(md_path):
            print(f"  ⚠️  MD 不存在")
            continue

        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        questions = parse_md_to_questions(md_text)
        total_parsed = len(questions)
        print(f"  解析: {total_parsed} 題")

        if not questions:
            print(f"  ⚠️  無題目")
            continue

        # ── Step A: 記錄 LLM 幻覺答案（僅供參考）──
        llm_answers = {
            str(q["question_number"]): q.get("correct_answer", "")
            for q in questions if q.get("correct_answer") in "ABCD"
        }
        print(f"  LLM 幻覺答案: {len(llm_answers)} 題（將丟棄）")

        # ── Step B: 清除所有答案 ──
        for q in questions:
            q["correct_answer"] = ""
            q["answer_source"] = ""

        # ── Step C: 從答案卷 PDF 提取答案（唯一來源）──
        answer_ref = {}
        if answer_pdf and os.path.exists(answer_pdf):
            print(f"  答案卷: {os.path.basename(answer_pdf)}")
            try:
                ans_text = _call_gemini_with_pdf(client, answer_pdf,
                    '提取所有題號和答案，回傳 JSON：{"answers": {"1": "A", "2": "B", ...}}')
                json_match = re.search(r'\{[\s\S]*\}', ans_text)
                if json_match:
                    answer_ref = json.loads(json_match.group()).get("answers", {})
                    for q in questions:
                        num_str = str(q["question_number"])
                        if num_str in answer_ref and isinstance(answer_ref[num_str], str) and answer_ref[num_str] in "ABCD":
                            q["correct_answer"] = answer_ref[num_str]
                            q["answer_source"] = "answer_pdf"
            except Exception as e:
                print(f"  ⚠️  Gemini 答案提取失敗: {str(e)[:80]}")
                try:
                    import pdfplumber
                    with pdfplumber.open(answer_pdf) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text() or ""
                            pairs = re.findall(r'(\d{1,3})\s+([A-D])', text)
                            for num_str, ans in pairs:
                                num = int(num_str)
                                if 1 <= num <= 200:
                                    answer_ref[str(num)] = ans
                    for q in questions:
                        num_str = str(q["question_number"])
                        if num_str in answer_ref and isinstance(answer_ref[num_str], str) and answer_ref[num_str] in "ABCD":
                            q["correct_answer"] = answer_ref[num_str]
                            q["answer_source"] = "answer_pdf_pdfplumber"
                except Exception as e2:
                    print(f"  ⚠️  pdfplumber 也失敗: {str(e2)[:80]}")
            time.sleep(REQUEST_DELAY_SEC)
        else:
            print(f"  ⚠️  無答案卷")

        # 統計
        answered = sum(1 for q in questions if q["correct_answer"] in "ABCD")
        excluded = total_parsed - answered
        print(f"  答案覆蓋: {answered}/{total_parsed} 題有答案，{excluded} 題排除")

        # ── 過濾無答案題目 ──
        valid_questions = [q for q in questions if q.get("correct_answer") in "ABCD"]

        # ── 4 層驗證 ──
        # L1: 結構
        v1 = validate_structure(questions, expected_count=0)
        print(f"  L1 結構: {'✅ PASS' if v1.passed else '❌ FAIL'} — 錯誤:{len(v1.errors)} 警告:{len(v1.warnings)}")

        # L2: 答案覆蓋率
        v2 = validate_answers_cross_check_v2(questions, answer_ref, llm_answers=llm_answers)
        print(f"  L2 覆蓋: {'✅ PASS' if v2.passed else '❌ FAIL'} — "
              f"有答案:{v2.stats.get('questions_with_answer')}/{v2.stats.get('total_questions')} "
              f"覆蓋率:{v2.stats.get('answer_coverage', 'N/A')}")

        # L3: 抽樣覆核（用有答案的題目）
        time.sleep(REQUEST_DELAY_SEC)
        v3 = validate_sampling(client, pdf_path, valid_questions)
        print(f"  L3 抽樣: {'✅ PASS' if v3.passed else '❌ FAIL'} — "
              f"抽樣:{v3.stats.get('sampled')} 問題:{v3.stats.get('issues')}")

        # L4: 統計
        v4 = validate_statistics(valid_questions)
        print(f"  L4 統計: {'✅ PASS' if v4.passed else '❌ FAIL'} — 警告:{len(v4.warnings)}")

        # 彙總
        validations = [v1, v2, v3, v4]
        all_passed = all(v.passed for v in validations)
        new_flag = "ok" if all_passed else "review"
        old_flag = entry.get("quality_flag", "?")

        # ── 更新 JSON（只存有答案的題目）──
        if json_path and os.path.exists(os.path.dirname(json_path)):
            meta = {
                "source_pdf": os.path.basename(pdf_path),
                "content_type": "exam",
                "total_questions_parsed": total_parsed,
                "valid_questions": len(valid_questions),
                "excluded_no_answer": excluded,
                "bloom_distribution": dict(Counter(q.get("bloom_category", "remember") for q in valid_questions)),
                "quality_flag": new_flag,
                "validations": [v.to_dict() for v in validations],
                "model": GEMINI_MODEL,
            }
            result_json = {"import_meta": meta, "questions": valid_questions}
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)

        # ── 更新 Manifest ──
        entry["quality_flag"] = new_flag
        entry["total_parsed"] = total_parsed
        entry["questions"] = len(valid_questions)
        entry["excluded_no_answer"] = excluded
        entry["with_answers"] = len(valid_questions)
        entry["validation_summary"] = {
            "L1_structure": "PASS" if v1.passed else "FAIL",
            "L2_answer_coverage": "PASS" if v2.passed else "FAIL",
            "L3_sampling": "PASS" if v3.passed else "FAIL",
            "L4_statistics": "PASS" if v4.passed else "FAIL",
        }
        entry["converter"] = "gemini_pdf_converter_v3"
        entry["revalidated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

        change = f"{old_flag} → {new_flag}"
        if old_flag != new_flag:
            change += " 🔄"
        print(f"  結果: {change} | 有效題庫: {len(valid_questions)} 題")

        results_summary.append({
            "file": key,
            "old": old_flag, "new": new_flag,
            "parsed": total_parsed, "valid": len(valid_questions), "excluded": excluded,
            "l1": "PASS" if v1.passed else "FAIL",
            "l2": "PASS" if v2.passed else "FAIL",
            "l3": "PASS" if v3.passed else "FAIL",
            "l4": "PASS" if v4.passed else "FAIL",
        })

    # 儲存 Manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 總結
    print(f"\n{'='*70}")
    print(f"  重新驗證完成（v3：答案卷唯一來源）")
    print(f"{'='*70}")

    ok_count = sum(1 for r in results_summary if r["new"] == "ok")
    review_count = sum(1 for r in results_summary if r["new"] == "review")
    improved = sum(1 for r in results_summary if r["old"] == "review" and r["new"] == "ok")
    total_valid = sum(r["valid"] for r in results_summary)
    total_excluded = sum(r["excluded"] for r in results_summary)
    total_parsed_all = sum(r["parsed"] for r in results_summary)

    print(f"\n  驗證: {len(results_summary)} 份")
    print(f"  ✅ ok: {ok_count} | ⚠️ review: {review_count} | 🔄 改善: {improved}")
    print(f"  題庫: {total_valid}/{total_parsed_all} 題有效（{total_excluded} 題無答案已排除）")

    print(f"\n  {'檔案':<55} {'解析':>4} {'有效':>4} {'排除':>4} {'舊':>6} {'新':>6}  L1  L2  L3  L4")
    print(f"  {'-'*110}")
    for r in results_summary:
        m = "🔄" if r["old"] != r["new"] else "  "
        print(f"  {r['file']:<55} {r['parsed']:>4} {r['valid']:>4} {r['excluded']:>4} "
              f"{r['old']:>6} {r['new']:>6}  {r['l1']:<4} {r['l2']:<4} {r['l3']:<4} {r['l4']:<4} {m}")

    print(f"\n  Manifest + JSON 已更新")


if __name__ == "__main__":
    revalidate_all()
