#!/usr/bin/env python3
"""測試 Haiku JSON 抽取器在三種差異大的 PDF 上的表現。

並行跑：
  1. 普考 401/Q_0302（法學+英文）
  2. iPAS 中級 ML（數學公式密集）
  3. 高考 201/Q_0301（高考專業科目）
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from claude_json_prototype import (  # type: ignore
    extract_questions, extract_answer_map, BACKEND,
)


TESTS = [
    {
        "name": "普考法學+英文 401/0302",
        "q_pdf": BACKEND / "data/historical_questions/_pdf/114080/401/Q_0302.pdf",
        "s_pdf": BACKEND / "data/historical_questions/_pdf/114080/401/S_0302.pdf",
        "out": "/tmp/test_moex_0302.json",
    },
    {
        "name": "iPAS 中級 ML",
        "q_pdf": BACKEND / "data/historical_questions/ipas/ai_planner/114_ai_mid_ml.pdf",
        "s_pdf": None,  # iPAS 單檔內嵌答案
        "out": "/tmp/test_ipas_ml.json",
    },
    {
        "name": "高考 201/0301",
        "q_pdf": BACKEND / "data/historical_questions/_pdf/114080/201/Q_0301.pdf",
        "s_pdf": BACKEND / "data/historical_questions/_pdf/114080/201/S_0301.pdf",
        "out": "/tmp/test_moex_201_0301.json",
    },
]


def run_test(t):
    t0 = time.time()
    try:
        qs = extract_questions(t["q_pdf"])
        if t["s_pdf"]:
            ans = extract_answer_map(t["s_pdf"])
            for q in qs:
                key = str(q["question_number"])
                if key in ans:
                    q["correct_answer"] = ans[key]
        with_ans = sum(1 for q in qs if q.get("correct_answer"))
        Path(t["out"]).write_text(json.dumps(qs, ensure_ascii=False, indent=2))
        return {
            "name": t["name"],
            "ok": True,
            "total": len(qs),
            "with_ans": with_ans,
            "time": time.time() - t0,
            "out": t["out"],
            "sample": qs[0] if qs else None,
        }
    except Exception as e:
        return {"name": t["name"], "ok": False, "error": str(e), "time": time.time() - t0}


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = [ex.submit(run_test, t) for t in TESTS]
        results = [f.result() for f in as_completed(futs)]

    print("\n" + "=" * 70)
    print("三份 PDF 測試結果")
    print("=" * 70)
    for r in results:
        print(f"\n▸ {r['name']}（{r['time']:.1f}s）")
        if r["ok"]:
            print(f"  ✓ {r['total']} 題，{r['with_ans']} 題有答案 → {r['out']}")
            if r["sample"]:
                s = r["sample"]
                print(f"  Q1: {s['content'][:80]}...")
                print(f"    A: {s['option_a'][:50]}")
                print(f"    答: {s['correct_answer']}")
        else:
            print(f"  ✗ 失敗：{r['error']}")
