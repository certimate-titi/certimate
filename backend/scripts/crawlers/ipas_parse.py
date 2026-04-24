#!/usr/bin/env python3
"""iPAS 考題解析（單檔含內嵌答案，無 S PDF）。

掃描 data/historical_questions/ipas/*/*.pdf → 用 claude_pdf_extract 抽題 +
figure + 可選 reviewer → 輸出 {pdf_stem}.json 到同目錄。
"""
import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claude_pdf_extract import HAIKU, extract_subject  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BACKEND = Path(__file__).resolve().parent.parent.parent
IPAS_ROOT = BACKEND / "data" / "historical_questions" / "ipas"


def parse_one(pdf: Path, run_review: bool) -> dict:
    out_file = pdf.parent / f"{pdf.stem}.json"
    figures_dir = pdf.parent / "figures" / pdf.stem

    result = extract_subject(q_pdf=pdf, s_pdf=None, figures_dir=figures_dir,
                             run_review=run_review)
    questions = result["questions"]
    for q in questions:
        paths = q.pop("figure_paths", [])
        q["figure_urls"] = [str(Path(p).relative_to(pdf.parent)) for p in paths]
        q.setdefault("type", "single_choice")
        q.setdefault("explanation", "")
        q.setdefault("bloom_category", None)

    output = {
        "import_meta": {
            "source": "iPAS 產業人才能力鑑定",
            "exam_code": "IPAS",
            "category_code": pdf.parent.name,
            "subject_code": pdf.stem,
            "total_questions": len(questions),
            "questions_with_answer": sum(1 for q in questions if q["correct_answer"]),
            "questions_with_figure": sum(1 for q in questions if q["figure_urls"]),
            "extractor": f"claude-cli/{HAIKU}",
        },
        "questions": questions,
    }
    if "review" in result:
        output["review"] = result["review"]
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    return {
        "pdf": pdf.name,
        "total": len(questions),
        "with_answer": sum(1 for q in questions if q["correct_answer"]),
        "with_figure": sum(1 for q in questions if q["figure_urls"]),
        "out": str(out_file),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--pattern", default="*.pdf", help="檔名過濾")
    args = ap.parse_args()

    pdfs = sorted(IPAS_ROOT.rglob(args.pattern))
    if not args.force:
        pdfs = [p for p in pdfs if not (p.parent / f"{p.stem}.json").exists()]

    if not pdfs:
        log.info("沒有待解析的 PDF（加 --force 強制重跑）")
        return

    log.info(f"待解析 {len(pdfs)} 份，workers={args.workers}，review={args.review}")
    t0 = time.time()
    ok, fail = 0, 0
    failed_log = IPAS_ROOT / "_failed.log"

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(parse_one, p, args.review): p for p in pdfs}
        for f in as_completed(futs):
            p = futs[f]
            try:
                s = f.result()
                ok += 1
                log.info(f"  ✓ {s['pdf']} — {s['total']} 題，答案 {s['with_answer']}，含圖 {s['with_figure']}")
            except Exception as e:
                fail += 1
                log.error(f"  ✗ {p.name}: {e}")
                with open(failed_log, "a", encoding="utf-8") as fh:
                    fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}\t{p}\t{e}\n")

    log.info(f"\n完成 {ok}/{len(pdfs)}（失敗 {fail}），耗時 {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
