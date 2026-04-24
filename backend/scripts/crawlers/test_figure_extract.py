#!/usr/bin/env python3
"""POC：C 方案 — PyMuPDF 抽 PDF 嵌入圖像 + Claude 題目-圖片配對。

目標：
  1. 從 iPAS ML PDF 抽出所有嵌入圖像（PNG/JPEG）
  2. 叫 Claude 抽題目時多輸出 figure_page（若有圖），讓配對邏輯用得上
  3. 依 bbox y 座標把圖配到對應題號
  4. 驗證 Q50 能正確配到那張 loss 曲線圖
"""
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict

import fitz  # PyMuPDF

BACKEND = Path(__file__).resolve().parent.parent.parent
DEFAULT_PDF = BACKEND / "data/historical_questions/ipas/ai_planner/114_ai_mid_ml.pdf"
PDF = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PDF
OUT_DIR = Path(f"/tmp/figure_poc_{PDF.stem}")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Step 1：PyMuPDF 抽圖 ───────────────────────────────────

# 雜訊過濾閾值
MIN_WIDTH = 200
MIN_HEIGHT = 150
MIN_AREA = 50000  # 像素面積
MAX_ASPECT_RATIO = 8.0  # 長寬比超過 8 視為 banner/裝飾


def _is_noise(img: Dict) -> bool:
    """判斷是否為雜訊圖（logo、banner、裝飾）。"""
    w, h = img["width"], img["height"]
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return True
    if w * h < MIN_AREA:
        return True
    ratio = max(w, h) / min(w, h)
    if ratio > MAX_ASPECT_RATIO:
        return True
    return False


def extract_images_from_pdf(pdf_path: Path, out_dir: Path) -> List[Dict]:
    """抽出 PDF 嵌入圖像並過濾雜訊。回傳按頁排序、同頁按 y 座標排序的列表。

    每張圖附 `index_on_page`（該頁第幾張有效圖，從 1 開始，由上到下）。
    """
    doc = fitz.open(pdf_path)
    raw = []
    for page_num, page in enumerate(doc, 1):
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            bbox = rects[0]
            base_image = doc.extract_image(xref)
            raw.append({
                "page": page_num,
                "xref": xref,
                "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                "width": base_image["width"],
                "height": base_image["height"],
                "ext": base_image["ext"],
                "bytes": base_image["image"],
            })

    # 過濾雜訊，分頁按 y0 排序，分配 index_on_page
    results = []
    filtered = [r for r in raw if not _is_noise(r)]
    noise_count = len(raw) - len(filtered)
    # 依頁分組
    by_page: Dict[int, List[Dict]] = {}
    for img in filtered:
        by_page.setdefault(img["page"], []).append(img)
    for page_num, imgs in by_page.items():
        imgs.sort(key=lambda r: r["bbox"][1])  # y0 由上到下
        for idx, img in enumerate(imgs, 1):
            out_path = out_dir / f"page{page_num:02d}_img{idx:02d}.{img['ext']}"
            out_path.write_bytes(img["bytes"])
            results.append({
                "page": page_num,
                "index_on_page": idx,
                "bbox": img["bbox"],
                "path": str(out_path),
                "width": img["width"],
                "height": img["height"],
                "ext": img["ext"],
            })
    doc.close()
    results.sort(key=lambda r: (r["page"], r["index_on_page"]))
    print(f"  [過濾] 原始 {len(raw)} 張 → 有效 {len(results)} 張（濾除雜訊 {noise_count} 張）")
    return results


# ── Step 2：Claude 抽題 + figure_page ─────────────────────

UNIFIED_PROMPT = """請使用 Read 工具讀取以下 PDF，逐題抽取成結構化 JSON。

輸出格式：JSON 陣列，每題一個 object：
[
  {
    "question_number": 1,
    "content": "題幹（含圖表描述、程式碼、閱讀原文等完整內容，不含選項）",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A/B/C/D 或 空字串",
    "has_figure": true/false,
    "figure_page": 圖所在頁碼（整數，1-based）; 無圖則 null,
    "figure_index_on_page": 若該頁有多張圖，本題用的是由上到下數第幾張（1-based 整數）; 無圖或該頁只有 1 張圖則填 1 或 null,
    "figure_description": "詳細描述圖內容（軸、標籤、趨勢等）; 無圖則空字串"
  }
]

重要規則：
1. 忠實抽取題幹、選項，不改寫、不省略
2. 若題目有圖/表/示意圖/示例代碼輸出：
   - has_figure=true
   - figure_page: 圖在 PDF 第幾頁
   - figure_index_on_page: 若該頁有多題都有圖，本題是**該頁由上到下第幾張**（1, 2, 3...）；只有一張則填 1
3. 閱讀原文、程式碼、情境敘述須完整納入 content
4. 只處理單選題，排除申論題、複選題
5. 題號用 PDF 原題號
6. 選項 PDF 原文可能用 ①②③④ 或 (A)(B)(C)(D)，一律對應 option_a/b/c/d
7. **選項完整性（硬性規定）**：
   - content 絕對不得包含 (A)(B)(C)(D) 或 ABCD 的選項文字，必須完全拆到 option_a~d 欄位
   - 若原 PDF 把選項擠在題幹段落中，仍必須拆出來放到 option_a~d
   - 若選項本身是圖片（例：四段程式碼/四張圖以截圖呈現為 A/B/C/D）：
     * option_a~d 填該選項的**實質摘要或轉錄**（例：程式碼第一行 + 關鍵差異），不可只填「程式碼 A」「選項 A」這種空標籤
     * 若真的無法轉錄，至少用 figure_description 詳述四個選項的差異
   - option_a~d 絕對不可互相複製（如「見上述 A」「同選項 A」），每個欄位必須是該選項的獨立內容
8. 只輸出 JSON 陣列，不要 markdown、不要說明

PDF 路徑：__PDF_PATH__"""


def run_claude(prompt: str, timeout: int = 900, model: str = "claude-haiku-4-5") -> str:
    cmd = ["claude", "-p", prompt, "--model", model,
           "--allowedTools", "Read", "--output-format", "text"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude failed: {r.stderr[:300]}")
    s = r.stdout.strip()
    if s.startswith("```"):
        s = "\n".join(l for l in s.split("\n") if not l.strip().startswith("```")).strip()
    return s


# ── Step 3：配對 ─────────────────────────────────────────

_rendered_pages: Dict[int, str] = {}


def render_page_fallback(pdf_path: Path, page_num: int, out_dir: Path, dpi: int = 150) -> str:
    """對向量繪圖或未嵌入圖像的頁面，整頁 render 成 PNG 當 fallback。"""
    if page_num in _rendered_pages:
        return _rendered_pages[page_num]
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    out_path = out_dir / f"page{page_num:02d}_fullrender.png"
    pix.save(out_path)
    doc.close()
    _rendered_pages[page_num] = str(out_path)
    return str(out_path)


def pair_figures_to_questions(questions: list, images: list, pdf_path: Path, out_dir: Path) -> list:
    """依 figure_page + figure_index_on_page 精準配對。

    無有效 index → 退回該頁所有嵌入圖。
    該頁完全沒有嵌入圖（向量繪圖）→ render 整頁作 fallback。
    """
    by_page: Dict[int, List[Dict]] = {}
    for img in images:
        by_page.setdefault(img["page"], []).append(img)
    for imgs in by_page.values():
        imgs.sort(key=lambda x: x["index_on_page"])

    for q in questions:
        if not q.get("has_figure") or not q.get("figure_page"):
            q["figure_paths"] = []
            continue
        page = q["figure_page"]
        imgs = by_page.get(page, [])
        idx = q.get("figure_index_on_page")
        if idx and isinstance(idx, int) and 1 <= idx <= len(imgs):
            q["figure_paths"] = [imgs[idx - 1]["path"]]
        elif imgs:
            q["figure_paths"] = [img["path"] for img in imgs]
            q["_pairing_fallback"] = "all_page_images"
        else:
            # 該頁沒有嵌入圖像 → render 整頁
            q["figure_paths"] = [render_page_fallback(pdf_path, page, out_dir)]
            q["_pairing_fallback"] = "page_render"
    return questions


# ── Step 4：出題老師 Reviewer ──────────────────────────

REVIEWER_PROMPT = """你是一位資深出題老師，專門審核選擇題題庫品質。

以下是從 PDF 抽取出來的選擇題 JSON（抽取工具是 AI），請你扮演**出題委員**，對每題做品質審核。

審核維度（每題逐項檢查）：
1. **題幹完整性**：題目意思是否完整？若是閱讀測驗／情境題，原文／情境敘述是否保留？
2. **選項品質**：A/B/C/D 是否都非空、語意完整、長度合理（不是只有單字或破碎文字）？
3. **答案合法**：correct_answer 是否為 A/B/C/D 其一或空字串？
4. **圖表一致**：若題幹含「下圖」「依圖」「依表」，has_figure 是否為 true？figure_description 是否有內容？
5. **題目類型**：是否為單選題？若混入複選題（題幹含「下列何者為非正確」「下列正確的有」等關鍵字）應標註
6. **內容正常**：題幹是否有 OCR 雜訊、亂碼、重複片段、選項混入題幹等污染？

輸出 JSON 格式（嚴格遵守）：
{
  "summary": {
    "total": 題數,
    "pass": 無問題題數,
    "warn": 有警告題數,
    "fail": 嚴重問題題數
  },
  "reviews": [
    {
      "question_number": 題號,
      "status": "pass" | "warn" | "fail",
      "findings": ["簡述問題 1", "簡述問題 2"]  // pass 則空陣列
    }
  ]
}

規則：
- `pass`: 完全符合規格，可直接上架
- `warn`: 有瑕疵但可用（例：答案空、figure_description 短但 has_figure=true）
- `fail`: 不可用（例：選項缺失、題幹殘缺、混入複選題、OCR 亂碼）
- findings 只列真實問題，不要湊數
- 只輸出 JSON，不要 markdown、不要前言

被審核的題目 JSON：
__QUESTIONS_JSON__
"""


def review_questions(questions: list, model: str = "claude-sonnet-4-6") -> dict:
    """用 Sonnet 當出題老師審核（品質要求高用 Sonnet）。"""
    prompt = REVIEWER_PROMPT.replace(
        "__QUESTIONS_JSON__",
        json.dumps(questions, ensure_ascii=False, indent=2),
    )
    t0 = time.time()
    raw = run_claude(prompt, timeout=600, model=model)
    print(f"  Reviewer 耗時 {time.time()-t0:.1f}s，{len(raw)} chars")
    return json.loads(raw)


# ── 主流程 ───────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Step 1: PyMuPDF 抽出所有嵌入圖像")
    print("=" * 60)
    t0 = time.time()
    images = extract_images_from_pdf(PDF, OUT_DIR)
    print(f"耗時 {time.time()-t0:.1f}s，共抽出 {len(images)} 張圖")
    for img in images:
        print(f"  page {img['page']}: {img['width']}x{img['height']} {img['ext']} → {img['path']}")

    print("\n" + "=" * 60)
    print("Step 2: Claude 抽題 + figure_page 標注")
    print("=" * 60)
    t0 = time.time()
    raw = run_claude(UNIFIED_PROMPT.replace("__PDF_PATH__", str(PDF.resolve())))
    print(f"耗時 {time.time()-t0:.1f}s，{len(raw)} chars")
    questions = json.loads(raw)
    print(f"抽出 {len(questions)} 題")
    figure_qs = [q for q in questions if q.get("has_figure")]
    print(f"含圖題目：{len(figure_qs)} 題")
    for q in figure_qs:
        print(f"  Q{q['question_number']} → page {q.get('figure_page')}")

    print("\n" + "=" * 60)
    print("Step 3: 配對題目與圖檔")
    print("=" * 60)
    questions = pair_figures_to_questions(questions, images, PDF, OUT_DIR)
    for q in figure_qs:
        q_new = next(x for x in questions if x["question_number"] == q["question_number"])
        print(f"  Q{q['question_number']}: {q_new.get('figure_paths', [])}")

    print("\n" + "=" * 60)
    print("Q50 驗證")
    print("=" * 60)
    q50 = next((q for q in questions if q["question_number"] == 50), None)
    if q50:
        print(f"has_figure: {q50.get('has_figure')}")
        print(f"figure_page: {q50.get('figure_page')}")
        print(f"figure_paths: {q50.get('figure_paths')}")
        print(f"figure_description 前 200: {q50.get('figure_description', '')[:200]}")

    print("\n" + "=" * 60)
    print("Step 4: 出題老師 Reviewer 審核")
    print("=" * 60)
    try:
        review = review_questions(questions)
        s = review.get("summary", {})
        print(f"  總計 {s.get('total')} 題：pass={s.get('pass')} warn={s.get('warn')} fail={s.get('fail')}")
        issues = [r for r in review.get("reviews", []) if r.get("status") != "pass"]
        for r in issues[:20]:
            print(f"  Q{r['question_number']} [{r['status']}]: {'; '.join(r.get('findings', []))}")
        Path(f"/tmp/figure_poc_{PDF.stem}_review.json").write_text(
            json.dumps(review, ensure_ascii=False, indent=2)
        )
    except Exception as e:
        print(f"  Reviewer 失敗：{e}")

    out = Path(f"/tmp/figure_poc_{PDF.stem}_result.json")
    out.write_text(json.dumps(questions, ensure_ascii=False, indent=2))
    print(f"\n完整結果 → {out}")


if __name__ == "__main__":
    main()
