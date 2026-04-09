"""
考選部歷年試題爬蟲（僅選擇題科目）

來源：考畢試題查詢平臺 https://wwwq.moex.gov.tw/exam/wFrmExamQandASearch.aspx
範圍：高考三級 / 普考 / 初等考試，最近三年（112-114），排除申論題

Usage:
    # Step 1: 抓取考試目錄（類科+科目清單）
    python -m scripts.crawlers.moex_crawler catalog --years 112-114

    # Step 2: 下載選擇題 PDF（有標準答案的科目）
    python -m scripts.crawlers.moex_crawler download --years 112-114

    # Step 3: 解析 PDF 為結構化 JSON
    python -m scripts.crawlers.moex_crawler parse

    # 一次全跑
    python -m scripts.crawlers.moex_crawler all --years 112-114
"""

import argparse
import json
import logging
import re
import sys
import time
import urllib3
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Suppress SSL warnings (考選部 SSL 憑證有問題)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── 常數 ──────────────────────────────────────────────────────────────────

BASE_URL = "https://wwwq.moex.gov.tw/exam"
SEARCH_URL = f"{BASE_URL}/wFrmExamQandASearch.aspx"
DOWNLOAD_URL = f"{BASE_URL}/wHandExamQandA_File.ashx"

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "historical_questions"
CATALOG_DIR = DATA_DIR / "_catalog"
PDF_DIR = DATA_DIR / "_pdf"

# 高普考+初等的考試代碼關鍵字
EXAM_KEYWORDS = ["高等考試三級", "普通考試", "初等考試"]

# 考試等級對照
EXAM_LEVEL_MAP = {
    "高等考試三級": "senior",
    "普通考試": "junior",
    "初等考試": "elementary",
}

REQUEST_DELAY = 1.5  # 秒，禮貌性延遲


# ── 資料結構 ──────────────────────────────────────────────────────────────

@dataclass
class Subject:
    code: str
    name: str
    has_answer: bool = False  # 是否有標準答案（選擇題指標）

@dataclass
class Category:
    code: str
    name: str
    subjects: list[Subject] = field(default_factory=list)

@dataclass
class ExamEvent:
    code: str           # e.g. "114080"
    name: str           # e.g. "114年公務人員高等考試三級考試暨普通考試"
    year: int           # ROC year, e.g. 114
    level: str          # "senior" / "junior" / "elementary"
    categories: list[Category] = field(default_factory=list)


# ── Session 管理 ─────────────────────────────────────────────────────────

class MoexSession:
    """管理與考選部網站的 ASP.NET WebForms 互動"""

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
        })
        self._viewstate = {}

    def _extract_aspnet_fields(self, soup: BeautifulSoup) -> dict:
        """提取 ASP.NET 隱藏欄位"""
        fields = {}
        for name in ["__VIEWSTATE", "__VIEWSTATEGENERATOR",
                      "__VIEWSTATEENCRYPTED", "__EVENTVALIDATION"]:
            tag = soup.find("input", {"name": name})
            if tag:
                fields[name] = tag.get("value", "")
        self._viewstate = fields
        return fields

    def init_search_page(self) -> BeautifulSoup:
        """載入搜尋頁面，取得初始 ViewState"""
        log.info("載入考畢試題查詢頁面...")
        resp = self.session.get(SEARCH_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        self._extract_aspnet_fields(soup)
        return soup

    def set_year_range(self, start_year: int, end_year: int) -> BeautifulSoup:
        """設定年份範圍，觸發考試代碼下拉選單更新"""
        log.info(f"設定年份範圍：{start_year}-{end_year}")
        data = {
            **self._viewstate,
            "ctl00$holderContent$wUctlExamYearStart$ddlExamYear": str(start_year),
            "ctl00$holderContent$wUctlExamYearEnd$ddlExamYear": str(end_year),
            "ctl00$holderContent$btnYear": "依考試年度設定考試簡稱",
        }
        time.sleep(REQUEST_DELAY)
        resp = self.session.post(SEARCH_URL, data=data, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        self._extract_aspnet_fields(soup)
        return soup

    def search_exam(self, exam_code: str) -> BeautifulSoup:
        """搜尋指定考試代碼的結果"""
        log.info(f"搜尋考試代碼：{exam_code}")
        data = {
            **self._viewstate,
            "ctl00$holderContent$ddlExamCode": exam_code,
            "ctl00$holderContent$btnSearch": "查詢",
        }
        time.sleep(REQUEST_DELAY)
        resp = self.session.post(SEARCH_URL, data=data, timeout=60)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        self._extract_aspnet_fields(soup)
        return soup

    def get_available_exams(self, soup: BeautifulSoup) -> list[tuple[str, str]]:
        """從下拉選單提取可用的考試代碼與名稱"""
        select = soup.find("select",
                           {"name": "ctl00$holderContent$ddlExamCode"})
        if not select:
            return []
        exams = []
        for opt in select.find_all("option"):
            code = opt.get("value", "").strip()
            name = opt.text.strip()
            if code and code != "0":
                exams.append((code, name))
        return exams

    def download_pdf(self, exam_code: str, category_code: str,
                     subject_code: str, file_type: str = "Q") -> Optional[bytes]:
        """
        下載 PDF
        file_type: Q=試題, S=答案, A=全部答案
        """
        params = {
            "t": file_type,
            "code": exam_code,
            "c": category_code,
            "s": subject_code,
            "q": "1",
        }
        try:
            time.sleep(REQUEST_DELAY)
            resp = self.session.get(DOWNLOAD_URL, params=params, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 500:
                content_type = resp.headers.get("Content-Type", "")
                if "pdf" in content_type.lower() or "octet" in content_type.lower():
                    return resp.content
        except Exception as e:
            log.warning(f"下載失敗 {exam_code}/{category_code}/{subject_code}: {e}")
        return None


# ── 結果解析 ──────────────────────────────────────────────────────────────

def parse_search_results(soup: BeautifulSoup) -> list[dict]:
    """
    解析搜尋結果表格，提取類科、科目、是否有答案連結

    結果表格結構：
    - 考試名稱 | 等級/類科 | 科目 | 試題(Q) | 測驗題答案(S) | 申論題答案 | ...
    """
    results = []
    table = soup.find("table", {"id": "ctl00_holderContent_gvExamQandA"})
    if not table:
        # 嘗試其他可能的 table id
        tables = soup.find_all("table", class_="gv")
        if tables:
            table = tables[0]

    if not table:
        log.warning("找不到結果表格")
        return results

    rows = table.find_all("tr")
    for row in rows[1:]:  # skip header
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        exam_info = cells[0].text.strip()
        category_info = cells[1].text.strip()
        subject_info = cells[2].text.strip()

        # 檢查是否有試題下載連結
        q_link = cells[3].find("a") if len(cells) > 3 else None
        # 檢查是否有測驗題答案下載連結（選擇題指標）
        s_link = cells[4].find("a") if len(cells) > 4 else None

        # 從連結提取 code/c/s 參數
        q_href = q_link.get("href", "") if q_link else ""
        s_href = s_link.get("href", "") if s_link else ""

        # 解析 URL 參數
        def extract_params(href):
            params = {}
            if "?" in href:
                query = href.split("?", 1)[1]
                for pair in query.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        params[k] = v
            return params

        q_params = extract_params(q_href)
        s_params = extract_params(s_href)

        results.append({
            "exam_info": exam_info,
            "category_info": category_info,
            "subject_info": subject_info,
            "has_question": bool(q_link),
            "has_answer": bool(s_link),
            "exam_code": q_params.get("code", s_params.get("code", "")),
            "category_code": q_params.get("c", s_params.get("c", "")),
            "subject_code": q_params.get("s", s_params.get("s", "")),
        })

    return results


def parse_results_to_events(results: list[dict], exam_code: str,
                            exam_name: str) -> list[Category]:
    """將搜尋結果整理為 Category + Subject 結構"""
    categories = {}

    for r in results:
        cat_code = r["category_code"]
        sub_code = r["subject_code"]
        if not cat_code or not sub_code:
            continue

        if cat_code not in categories:
            categories[cat_code] = Category(
                code=cat_code,
                name=r["category_info"],
            )

        categories[cat_code].subjects.append(Subject(
            code=sub_code,
            name=r["subject_info"],
            has_answer=r["has_answer"],
        ))

    return list(categories.values())


# ── 指令：catalog ────────────────────────────────────────────────────────

def probe_exam_catalog(start_year: int, end_year: int):
    """
    透過無狀態探測，列舉所有考試代碼、類科、科目組合
    檢查哪些有標準答案（t=S）= 選擇題指標
    """
    s = requests.Session()
    s.verify = False
    s.headers.update({"User-Agent": "Mozilla/5.0"})

    # 已知的類科範圍（從研究結果得知）
    category_ranges = {
        "elementary": range(501, 517),     # 501-516
        "junior": range(401, 456),         # 401-455
        "senior": range(201, 301),         # 201-300
    }

    level_labels = {
        "elementary": "初等考試",
        "junior": "普通考試",
        "senior": "高等考試三級",
    }

    # 常見科目代碼
    common_subjects = [
        "0101", "0102",  # 國文
        "0401", "0402",  # 法學知識與英文
        "0301", "0302",  # 政治學
        "0303", "0304",  # 行政學
        "0305", "0306",  # 公共政策
        "0403", "0404", "0405", "0406",  # 專業科目
        "0407", "0408", "0409", "0410",
        "0501", "0502", "0503", "0504",
    ]

    all_events = []
    download_url = f"{BASE_URL}/wHandExamQandA_File.ashx"

    for year in range(start_year, end_year + 1):
        log.info(f"\n{'='*60}")
        log.info(f"民國 {year} 年")

        # 初等考試
        level = "elementary"
        exam_code = f"{year}010"
        categories_in_event = {}

        log.info(f"  {level_labels[level]}: {exam_code}")
        for cat_code in category_ranges[level]:
            cat_code_str = str(cat_code)
            mc_subjects = {}

            for sub_code in common_subjects:
                # 檢查是否有答案（選擇題）
                try:
                    time.sleep(0.3)
                    resp = s.get(
                        download_url,
                        params={"t": "S", "code": exam_code, "c": cat_code_str, "s": sub_code, "q": "1"},
                        timeout=10,
                    )
                    if resp.status_code == 200 and len(resp.content) > 300:
                        # 有答案 = 選擇題
                        mc_subjects[sub_code] = True
                except Exception as e:
                    pass

            if mc_subjects:
                categories_in_event[cat_code_str] = list(mc_subjects.keys())
                log.info(f"    類科 {cat_code}: {len(mc_subjects)} 個選擇題")

        if categories_in_event:
            event_categories = []
            for cat_code, subject_codes in categories_in_event.items():
                subjects = [Subject(code=sc, name=f"科目{sc}", has_answer=True)
                           for sc in subject_codes]
                event_categories.append(Category(code=cat_code, name=f"類科{cat_code}",
                                                subjects=subjects))
            event = ExamEvent(code=exam_code, name=f"民國{year}初等考試",
                            year=year, level=level, categories=event_categories)
            all_events.append(event)

        # 高考三級 + 普考（同一考試事件）
        level = "senior"
        exam_code = f"{year}080"
        categories_in_event = {"senior": {}, "junior": {}}

        log.info(f"  高考三級 + 普考: {exam_code}")

        # 高考（201-300）
        for cat_code in category_ranges["senior"]:
            cat_code_str = str(cat_code)
            mc_subjects = {}

            for sub_code in common_subjects:
                try:
                    time.sleep(0.3)
                    resp = s.get(
                        download_url,
                        params={"t": "S", "code": exam_code, "c": cat_code_str, "s": sub_code, "q": "1"},
                        timeout=10,
                    )
                    if resp.status_code == 200 and len(resp.content) > 300:
                        mc_subjects[sub_code] = True
                except Exception as e:
                    pass

            if mc_subjects:
                categories_in_event["senior"][cat_code_str] = list(mc_subjects.keys())

        # 普考（401-455）
        for cat_code in category_ranges["junior"]:
            cat_code_str = str(cat_code)
            mc_subjects = {}

            for sub_code in common_subjects:
                try:
                    time.sleep(0.3)
                    resp = s.get(
                        download_url,
                        params={"t": "S", "code": exam_code, "c": cat_code_str, "s": sub_code, "q": "1"},
                        timeout=10,
                    )
                    if resp.status_code == 200 and len(resp.content) > 300:
                        mc_subjects[sub_code] = True
                except Exception as e:
                    pass

            if mc_subjects:
                categories_in_event["junior"][cat_code_str] = list(mc_subjects.keys())

        log.info(f"    高考三級: {len(categories_in_event['senior'])} 個類科")
        log.info(f"    普考: {len(categories_in_event['junior'])} 個類科")

        if categories_in_event["senior"] or categories_in_event["junior"]:
            event_categories = []
            for cat_code, subject_codes in categories_in_event["senior"].items():
                subjects = [Subject(code=sc, name=f"科目{sc}", has_answer=True)
                           for sc in subject_codes]
                event_categories.append(Category(code=cat_code, name=f"高考類科{cat_code}",
                                                subjects=subjects))
            for cat_code, subject_codes in categories_in_event["junior"].items():
                subjects = [Subject(code=sc, name=f"科目{sc}", has_answer=True)
                           for sc in subject_codes]
                event_categories.append(Category(code=cat_code, name=f"普考類科{cat_code}",
                                                subjects=subjects))
            event = ExamEvent(code=exam_code, name=f"民國{year}高等考試三級及普通考試",
                            year=year, level=level, categories=event_categories)
            all_events.append(event)

    # 儲存目錄
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    catalog_file = CATALOG_DIR / f"catalog_{start_year}-{end_year}.json"
    catalog_data = [asdict(ev) for ev in all_events]

    with open(catalog_file, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)

    log.info(f"\n目錄已儲存至 {catalog_file}")

    # 統計
    total_mc = sum(
        sum(len(c.subjects) for c in ev.categories)
        for ev in all_events
    )
    log.info(f"總計：{len(all_events)} 個考試事件，{total_mc} 個選擇題科目待下載")

    return all_events


def cmd_catalog(start_year: int, end_year: int):
    """抓取考試目錄（類科+科目清單），儲存為 JSON"""
    return probe_exam_catalog(start_year, end_year)


# ── 指令：download ───────────────────────────────────────────────────────

def cmd_download(start_year: int, end_year: int):
    """根據目錄下載選擇題 PDF（試題+答案）"""
    catalog_file = CATALOG_DIR / f"catalog_{start_year}-{end_year}.json"
    if not catalog_file.exists():
        log.error(f"目錄檔不存在：{catalog_file}，請先執行 catalog 指令")
        return

    with open(catalog_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    ms = MoexSession()
    downloaded = 0
    skipped = 0
    failed = 0

    for event in catalog:
        exam_code = event["code"]
        exam_name = event["name"]
        level = event["level"]

        for cat in event["categories"]:
            cat_code = cat["code"]
            cat_name = cat["name"]

            for sub in cat["subjects"]:
                sub_code = sub["code"]
                sub_name = sub["name"]
                has_answer = sub["has_answer"]

                if not has_answer:
                    continue

                # 建立目錄
                pdf_subdir = PDF_DIR / level / f"{exam_code}_{cat_code}"
                pdf_subdir.mkdir(parents=True, exist_ok=True)

                # 下載試題 PDF
                q_file = pdf_subdir / f"Q_{sub_code}.pdf"
                s_file = pdf_subdir / f"S_{sub_code}.pdf"

                if q_file.exists() and s_file.exists():
                    skipped += 1
                    continue

                log.info(f"下載：{exam_name} / {cat_name} / {sub_name}")

                if not q_file.exists():
                    q_data = ms.download_pdf(exam_code, cat_code, sub_code, "Q")
                    if q_data:
                        q_file.write_bytes(q_data)
                    else:
                        log.warning(f"  試題 PDF 下載失敗")
                        failed += 1
                        continue

                if not s_file.exists():
                    s_data = ms.download_pdf(exam_code, cat_code, sub_code, "S")
                    if s_data:
                        s_file.write_bytes(s_data)
                    else:
                        log.warning(f"  答案 PDF 下載失敗")

                downloaded += 1

                if downloaded % 50 == 0:
                    log.info(f"  進度：已下載 {downloaded} 組")

    log.info(f"\n下載完成：{downloaded} 組成功，{skipped} 組跳過（已存在），{failed} 組失敗")


# ── 指令：parse ──────────────────────────────────────────────────────────

def parse_mc_from_text(text: str) -> list[dict]:
    """
    從 PDF 文字中解析選擇題

    常見格式：
    1. 依信託法規定，下列何者非信託之法律特徵？
    (A) 信託財產之獨立性
    (B) 信託財產之公示性
    (C) 信託財產之永續性
    (D) 受益人之受益性
    """
    questions = []

    # 清理文字
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 匹配題號開頭的題目區塊
    # 支援 "1." "1、" "1 " "（1）" 等格式
    pattern = re.compile(
        r'(?:^|\n)\s*(\d{1,3})\s*[.、）\)]\s*(.+?)(?=\n\s*\d{1,3}\s*[.、）\)]|\Z)',
        re.DOTALL
    )

    for match in pattern.finditer(text):
        q_num = int(match.group(1))
        q_block = match.group(2).strip()

        # 分離題幹與選項
        # 選項格式：(A) / （A） / A. / (a)
        opt_pattern = re.compile(
            r'[\(（]\s*([A-Da-d])\s*[\)）]\.?\s*(.+?)(?=[\(（]\s*[A-Da-d]\s*[\)）]|\Z)',
            re.DOTALL
        )
        options = {}
        opt_matches = list(opt_pattern.finditer(q_block))

        if len(opt_matches) >= 2:
            # 題幹 = 選項之前的文字
            content = q_block[:opt_matches[0].start()].strip()
            for om in opt_matches:
                letter = om.group(1).upper()
                opt_text = om.group(2).strip().replace("\n", " ")
                options[letter] = opt_text
        else:
            content = q_block.strip()

        if content:
            questions.append({
                "question_number": q_num,
                "content": content.replace("\n", " ").strip(),
                "type": "single_choice",
                "option_a": options.get("A", ""),
                "option_b": options.get("B", ""),
                "option_c": options.get("C", ""),
                "option_d": options.get("D", ""),
                "correct_answer": "",
                "explanation": "",
                "bloom_category": None,
            })

    return questions


def parse_answer_key(text: str) -> dict[int, str]:
    """
    從答案 PDF 文字中解析標準答案

    常見格式：
    1.A  2.B  3.C  4.D  5.A
    或
    1 A  2 B  3 C
    """
    answers = {}
    # 匹配 "題號.答案" 或 "題號 答案"
    pattern = re.compile(r'(\d{1,3})\s*[.．、]\s*([A-Da-d])')
    for match in pattern.finditer(text):
        q_num = int(match.group(1))
        ans = match.group(2).upper()
        answers[q_num] = ans
    return answers


def cmd_parse():
    """解析已下載的 PDF 為結構化 JSON"""
    try:
        import pdfplumber
    except ImportError:
        log.error("需要 pdfplumber：pip install pdfplumber")
        return

    if not PDF_DIR.exists():
        log.error(f"PDF 目錄不存在：{PDF_DIR}，請先執行 download 指令")
        return

    # 載入目錄以取得 metadata
    catalog_files = list(CATALOG_DIR.glob("catalog_*.json"))
    catalog_lookup = {}
    for cf in catalog_files:
        with open(cf, "r", encoding="utf-8") as f:
            for event in json.load(f):
                for cat in event["categories"]:
                    for sub in cat["subjects"]:
                        key = f"{event['code']}_{cat['code']}_{sub['code']}"
                        catalog_lookup[key] = {
                            "exam_code": event["code"],
                            "exam_name": event["name"],
                            "exam_year": event["year"],
                            "level": event["level"],
                            "category_code": cat["code"],
                            "category_name": cat["name"],
                            "subject_code": sub["code"],
                            "subject_name": sub["name"],
                        }

    parsed_count = 0
    error_count = 0

    for level_dir in sorted(PDF_DIR.iterdir()):
        if not level_dir.is_dir() or level_dir.name.startswith("_"):
            continue

        for exam_cat_dir in sorted(level_dir.iterdir()):
            if not exam_cat_dir.is_dir():
                continue

            q_files = sorted(exam_cat_dir.glob("Q_*.pdf"))
            for q_file in q_files:
                sub_code = q_file.stem.replace("Q_", "")
                s_file = exam_cat_dir / f"S_{sub_code}.pdf"

                # 提取 exam_code 和 cat_code
                parts = exam_cat_dir.name.split("_", 1)
                if len(parts) != 2:
                    continue
                exam_code, cat_code = parts

                lookup_key = f"{exam_code}_{cat_code}_{sub_code}"
                meta = catalog_lookup.get(lookup_key, {})

                try:
                    # 解析試題 PDF
                    with pdfplumber.open(q_file) as pdf:
                        q_text = "\n".join(
                            page.extract_text() or "" for page in pdf.pages
                        )

                    questions = parse_mc_from_text(q_text)

                    # 解析答案 PDF
                    if s_file.exists():
                        with pdfplumber.open(s_file) as pdf:
                            s_text = "\n".join(
                                page.extract_text() or "" for page in pdf.pages
                            )
                        answer_key = parse_answer_key(s_text)

                        # 合併答案
                        for q in questions:
                            q_num = q["question_number"]
                            if q_num in answer_key:
                                q["correct_answer"] = answer_key[q_num]

                    # 輸出 JSON
                    level = meta.get("level", level_dir.name)
                    subject_slug = re.sub(r'[^\w]', '_', meta.get("subject_name", sub_code))
                    out_dir = DATA_DIR / level / meta.get("category_name", cat_code)
                    out_dir.mkdir(parents=True, exist_ok=True)

                    year = meta.get("exam_year", "unknown")
                    out_file = out_dir / f"{year}_{subject_slug}.json"

                    output = {
                        "import_meta": {
                            "source": "考選部考畢試題查詢平臺",
                            "exam_name": meta.get("exam_name", ""),
                            "exam_code": exam_code,
                            "exam_year": year,
                            "level": level,
                            "category_code": cat_code,
                            "category_name": meta.get("category_name", ""),
                            "subject_code": sub_code,
                            "subject_name": meta.get("subject_name", ""),
                            "total_questions": len(questions),
                            "questions_with_answer": sum(
                                1 for q in questions if q["correct_answer"]
                            ),
                        },
                        "questions": questions,
                    }

                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(output, f, ensure_ascii=False, indent=2)

                    parsed_count += 1
                    if parsed_count % 20 == 0:
                        log.info(f"  已解析 {parsed_count} 份")

                except Exception as e:
                    log.warning(f"解析失敗 {q_file}: {e}")
                    error_count += 1

    log.info(f"\n解析完成：{parsed_count} 份成功，{error_count} 份失敗")
    log.info(f"JSON 輸出位置：{DATA_DIR}")


# ── 主程式 ────────────────────────────────────────────────────────────────

def parse_year_range(year_str: str) -> tuple[int, int]:
    """解析年份範圍字串，如 '112-114'"""
    parts = year_str.split("-")
    if len(parts) == 2:
        return int(parts[0]), int(parts[1])
    elif len(parts) == 1:
        y = int(parts[0])
        return y, y
    else:
        raise ValueError(f"無法解析年份範圍：{year_str}")


def main():
    parser = argparse.ArgumentParser(description="考選部歷年試題爬蟲（選擇題）")
    parser.add_argument("command", choices=["catalog", "download", "parse", "all"],
                        help="執行指令")
    parser.add_argument("--years", default="112-114",
                        help="年份範圍（民國年），如 112-114")
    args = parser.parse_args()

    start_year, end_year = parse_year_range(args.years)
    log.info(f"目標年份：民國 {start_year}-{end_year} 年")

    if args.command == "catalog":
        cmd_catalog(start_year, end_year)
    elif args.command == "download":
        cmd_download(start_year, end_year)
    elif args.command == "parse":
        cmd_parse()
    elif args.command == "all":
        cmd_catalog(start_year, end_year)
        cmd_download(start_year, end_year)
        cmd_parse()


if __name__ == "__main__":
    main()
