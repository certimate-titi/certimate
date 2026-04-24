#!/usr/bin/env python3
"""Claude + PyMuPDF PDF 題目抽取工具組。

供 moex_simple.py / ipas 爬蟲與其他管線共用。

提供：
  - extract_questions_from_pdf   題目 PDF → 結構化 JSON（含 figure 標註）
  - extract_answer_map           答案 PDF → {題號: 答案}
  - extract_figures_from_pdf     PyMuPDF 抽嵌入圖像 + 噪音過濾
  - pair_figures_to_questions    依 figure_page + index_on_page 配對
  - review_questions             出題老師 reviewer（Sonnet 4.6）
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF

HAIKU = "claude-haiku-4-5"
SONNET = "claude-sonnet-4-6"

# 圖像噪音過濾閾值
MIN_WIDTH = 200
MIN_HEIGHT = 150
MIN_AREA = 50000
MAX_ASPECT_RATIO = 8.0


# ── Claude CLI ───────────────────────────────────────────────

def run_claude(prompt: str, timeout: int = 900, model: str = HAIKU) -> str:
    cmd = ["claude", "-p", prompt, "--model", model,
           "--allowedTools", "Read", "--output-format", "text"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"claude failed: {r.stderr[:300]}")
    s = r.stdout.strip()
    if s.startswith("```"):
        s = "\n".join(l for l in s.split("\n") if not l.strip().startswith("```")).strip()
    return s


# ── Step 1：PyMuPDF 抽嵌入圖像 ───────────────────────────────

def _is_noise(img: Dict) -> bool:
    w, h = img["width"], img["height"]
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return True
    if w * h < MIN_AREA:
        return True
    return max(w, h) / min(w, h) > MAX_ASPECT_RATIO


def extract_figures_from_pdf(pdf_path: Path, out_dir: Path) -> List[Dict]:
    """抽出 PDF 嵌入圖像、濾雜訊、依頁分配 index_on_page。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    raw = []
    for page_num, page in enumerate(doc, 1):
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            bbox = rects[0]
            base = doc.extract_image(xref)
            raw.append({
                "page": page_num, "xref": xref,
                "bbox": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                "width": base["width"], "height": base["height"],
                "ext": base["ext"], "bytes": base["image"],
            })

    filtered = [r for r in raw if not _is_noise(r)]
    by_page: Dict[int, List[Dict]] = {}
    for img in filtered:
        by_page.setdefault(img["page"], []).append(img)

    results = []
    for page_num, imgs in by_page.items():
        imgs.sort(key=lambda r: r["bbox"][1])  # y0 由上到下
        for idx, img in enumerate(imgs, 1):
            out_path = out_dir / f"page{page_num:02d}_img{idx:02d}.{img['ext']}"
            out_path.write_bytes(img["bytes"])
            results.append({
                "page": page_num, "index_on_page": idx,
                "bbox": img["bbox"], "path": str(out_path),
                "width": img["width"], "height": img["height"], "ext": img["ext"],
            })
    doc.close()
    results.sort(key=lambda r: (r["page"], r["index_on_page"]))
    return results


def render_page_fallback(pdf_path: Path, page_num: int, out_dir: Path, dpi: int = 150) -> str:
    """向量繪圖或無嵌入圖像時，整頁 render 成 PNG。"""
    out_path = out_dir / f"page{page_num:02d}_fullrender.png"
    if out_path.exists():
        return str(out_path)
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(out_path)
    doc.close()
    return str(out_path)


# ── Step 2：題目抽取 ─────────────────────────────────────────

QUESTIONS_PROMPT = """請使用 Read 工具讀取以下 PDF，逐題抽取成結構化 JSON。

輸出格式：JSON 陣列，每題一個 object：
[
  {
    "question_number": 1,
    "content": "題幹（含圖表描述、程式碼、閱讀原文等完整內容，不含選項）",
    "option_a": "...",
    "option_b": "...",
    "option_c": "...",
    "option_d": "...",
    "correct_answer": "A/B/C/D 或複選組合如 AC、ABD（字母由小到大排序）；無則空字串",
    "type": "single_choice" 或 "multiple_choice",
    "has_figure": true/false,
    "figure_page": 圖所在頁碼（整數，1-based）; 無圖則 null,
    "figure_index_on_page": 若該頁有多張圖，本題用的是由上到下數第幾張（1-based 整數）; 無圖或該頁只有 1 張圖則填 1 或 null,
    "figure_description": "詳細描述圖內容（軸、標籤、趨勢等）; 無圖則空字串"
  }
]

重要規則：
1. 忠實抽取題幹、選項，不改寫、不省略
1a. 題幹必須完整保留：若題目前方有「」或『』包住的閱讀原文、情境敘述、古文引述、長篇文字等，**整段完整納入 content 欄位**，不可只保留最後那句提問
2. 若題目有圖/表/示意圖/示例代碼輸出：
   - has_figure=true
   - figure_page: 圖在 PDF 第幾頁
   - figure_index_on_page: 若該頁有多題都有圖，本題是**該頁由上到下第幾張**（1, 2, 3...）；只有一張則填 1
3. 閱讀原文、程式碼、情境敘述須完整納入 content
4. 處理單選題與複選題，排除申論題/問答題/計算題
   - 複選題（「下列何者正確」「下列哪些」「正確的有」等）：type="multiple_choice"，correct_answer 填所有正確字母（如 "AC"、"ABD"）
   - 單選題：type="single_choice"，correct_answer 填單一字母
   - 若該 PDF 沒有任何可抽取的選擇題（全部申論），輸出空陣列 []
5. 題號用 PDF 原題號
6. 選項 PDF 原文可能用 ①②③④ 或 (A)(B)(C)(D)，一律對應 option_a/b/c/d
7. 選項完整性（硬性規定）：
   - content 絕對不得包含 (A)(B)(C)(D) 或 ABCD 的選項文字，必須完全拆到 option_a~d 欄位
   - 若選項本身是圖片（例：四段程式碼/四張圖以截圖呈現），option_a~d 填該選項的實質摘要或轉錄，不可只填「程式碼 A」空標籤
   - option_a~d 絕對不可互相複製（如「見上述 A」「同選項 A」）
8. 只輸出 JSON 陣列，不要 markdown、不要說明

PDF 路徑：__PDF_PATH__"""


ANSWER_MAP_PROMPT = """請使用 Read 工具讀取以下答案 PDF，抽取題號→答案對照。

輸出格式（JSON object）：
{"1": "A", "2": "BD", "3": "ACE"}

規則：
1. 單選題答案為單一字母（如 "A"）
2. 複選題答案保留所有正確字母，由小到大排序（如 "AC"、"ABD"）
3. 沒有答案的題號不要列出
4. 只輸出 JSON object，不要 markdown、不要說明

PDF 路徑：__PDF_PATH__"""


def extract_questions_from_pdf(pdf_path: Path, timeout: int = 900) -> List[Dict]:
    prompt = QUESTIONS_PROMPT.replace("__PDF_PATH__", str(pdf_path.resolve()))
    raw = run_claude(prompt, timeout=timeout)
    return json.loads(raw)


def extract_answer_map(pdf_path: Path, timeout: int = 600) -> Dict[str, str]:
    prompt = ANSWER_MAP_PROMPT.replace("__PDF_PATH__", str(pdf_path.resolve()))
    raw = run_claude(prompt, timeout=timeout)
    return json.loads(raw)


# ── Step 3：配對 ─────────────────────────────────────────────

def pair_figures_to_questions(questions: List[Dict], figures: List[Dict],
                              pdf_path: Path, out_dir: Path) -> List[Dict]:
    """依 figure_page + index_on_page 精準配對。

    無有效 index → 退回該頁所有嵌入圖。
    該頁完全沒嵌入圖 → render 整頁作 fallback。
    """
    by_page: Dict[int, List[Dict]] = {}
    for img in figures:
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
            q["figure_paths"] = [i["path"] for i in imgs]
            q["_pairing_fallback"] = "all_page_images"
        else:
            q["figure_paths"] = [render_page_fallback(pdf_path, page, out_dir)]
            q["_pairing_fallback"] = "page_render"
    return questions


# ── Step 4：出題老師 Reviewer ────────────────────────────────

REVIEWER_PROMPT = """你是一位資深出題老師，專門審核選擇題題庫品質。

以下是從 PDF 抽取出來的選擇題 JSON（抽取工具是 AI），請對每題做品質審核。

審核維度：
1. 題幹完整性：題目意思完整？閱讀測驗的原文是否保留？
2. 選項品質：A/B/C/D 都非空、語意完整、長度合理？
3. 答案合法：correct_answer 是 A/B/C/D 其一或空字串？
4. 圖表一致：若題幹含「下圖」「依圖」「依表」，has_figure 是 true 且 figure_description 有內容？
5. 題目類型：type 標註是否正確（單選 vs 複選）；複選題 correct_answer 是否為多字母；單選題 correct_answer 是否單字母
6. 內容正常：題幹是否有 OCR 雜訊、亂碼、重複片段、選項混入題幹等污染？

輸出 JSON 格式（嚴格遵守）：
{
  "summary": {"total": 題數, "pass": 無問題題數, "warn": 有警告題數, "fail": 嚴重問題題數},
  "reviews": [
    {"question_number": 題號, "status": "pass" | "warn" | "fail", "findings": ["簡述問題 1"]}
  ]
}

規則：
- pass：完全符合規格，可直接上架
- warn：有瑕疵但可用（例：答案空、figure_description 短但 has_figure=true）
- fail：不可用（例：選項缺失、題幹殘缺、OCR 亂碼、type 與 correct_answer 字母數不一致）
- findings 只列真實問題
- 只輸出 JSON，不要 markdown、不要前言

被審核的題目 JSON：
__QUESTIONS_JSON__
"""


def review_questions(questions: List[Dict], model: str = SONNET, timeout: int = 600) -> Dict:
    prompt = REVIEWER_PROMPT.replace(
        "__QUESTIONS_JSON__",
        json.dumps(questions, ensure_ascii=False, indent=2),
    )
    raw = run_claude(prompt, timeout=timeout, model=model)
    return json.loads(raw)


# ── 一站式 pipeline ─────────────────────────────────────────

def extract_subject(q_pdf: Path, s_pdf: Optional[Path], figures_dir: Path,
                    run_review: bool = False) -> Dict:
    """完整流程：抽題 + 答案合併 + figure 配對 + 可選 review。

    回傳：{questions, figures, review?}
    """
    figures = extract_figures_from_pdf(q_pdf, figures_dir)
    questions = extract_questions_from_pdf(q_pdf)

    if s_pdf is not None:
        ans = extract_answer_map(s_pdf)
        for q in questions:
            key = str(q["question_number"])
            if key in ans and not q.get("correct_answer"):
                q["correct_answer"] = ans[key]

    questions = pair_figures_to_questions(questions, figures, q_pdf, figures_dir)

    result = {"questions": questions, "figures": figures}
    if run_review:
        result["review"] = review_questions(questions)
    return result
