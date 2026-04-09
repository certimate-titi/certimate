#!/usr/bin/env python3
"""
自動 Catalog 生成器 — 掃描考選部所有可用的考試/類科/科目組合

策略：
1. 已知考試代碼模式：{年份}010=初等, {年份}080=高普考
2. 已知類科代碼範圍：初等 501-516, 普考 401-455, 高考 201-300
3. 對每個考試/類科/科目組合，試探 t=S (答案) URL
4. 若答案 PDF 存在（>500 bytes）= 選擇題 = 有效
5. 輸出為 YAML 供 moex_simple.py 使用

使用方式：
    python auto_catalog_generator.py --years 112 113 114 --output exam_catalog_complete.yaml

預期耗時：
    - 112-114 年，~ 1500 次 HTTP 檢查
    - 禮貌延遲 0.5 秒/次 = 約 750 秒 = 12 分鐘
    - 實際會更快（並行 + 快速失敗）
"""

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Set

import requests
import urllib3
import yaml

urllib3.disable_warnings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

DOWNLOAD_URL = "https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx"

# 已知的類科代碼範圍
CATEGORY_RANGES = {
    "elementary": list(range(501, 517)),    # 初等：501-516
    "junior": list(range(401, 456)),        # 普考：401-455
    "senior": list(range(201, 301)),        # 高考：201-300
}

# 常見科目代碼（可逐漸擴展）
# 格式：前 2 碼 = 科目大類，後 2 碼 = 編號
SUBJECT_CODE_PREFIXES = [
    "01",   # 國文/公民與英文
    "02",   # 政治學/行政學等
    "03",   # 法律類
    "04",   # 英文/法學知識等
    "05",   # 管理/安全衛生等
]

SUBJECT_CODE_SUFFIXES = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]

# 生成所有可能的科目代碼
POSSIBLE_SUBJECTS = [f"{p}{s}" for p in SUBJECT_CODE_PREFIXES for s in SUBJECT_CODE_SUFFIXES]


# ── 探測 ────────────────────────────────────────────────────────────────

class Prober:
    def __init__(self, max_workers: int = 8, request_delay: float = 0.3):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})
        self.max_workers = max_workers
        self.request_delay = request_delay
        self.last_request_time = 0

    def _throttle(self):
        """禮貌延遲"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self.last_request_time = time.time()

    def check_subject_exists(
        self, exam_code: str, cat_code: int, sub_code: str
    ) -> bool:
        """
        檢查科目是否存在（有標準答案 = 選擇題）
        使用 HEAD 請求節省帶寬
        """
        self._throttle()

        params = {
            "t": "S",  # 答案 PDF
            "code": exam_code,
            "c": str(cat_code),
            "s": sub_code,
            "q": "1",
        }

        try:
            # 先用 HEAD 試探
            resp = self.session.head(
                DOWNLOAD_URL, params=params, timeout=10, allow_redirects=False
            )

            # HEAD 失敗就試 GET （某些伺服器不支援 HEAD）
            if resp.status_code != 200:
                resp = self.session.get(
                    DOWNLOAD_URL, params=params, timeout=10, stream=True
                )
                if resp.status_code == 200:
                    # 只讀前 1KB 來檢查是否為有效 PDF
                    content = resp.content[:1024]
                    return len(content) > 500 and b"%PDF" in content
            else:
                # HEAD 成功
                return True

        except Exception:
            pass

        return False

    def scan_exam_year(
        self, year: int
    ) -> Dict[str, Dict[int, List[str]]]:
        """
        掃描某一年的所有考試（初等 + 高普考）

        回傳：
        {
            "elementary": {
                "exam_code": "114010",
                "categories": {
                    501: ["0101", "0102", "0501"],
                    502: ["0101", "0102", ...],
                }
            },
            "senior_junior": {
                "exam_code": "114080",
                "senior": {201: [...], ...},
                "junior": {401: [...], ...},
            }
        }
        """
        results = {}

        # ── 初等考試 ──
        elem_code = f"{year}010"
        log.info(f"\n掃描 {year} 年初等考試 ({elem_code})...")
        elem_cats = self._scan_categories(elem_code, CATEGORY_RANGES["elementary"])
        if elem_cats:
            results["elementary"] = {"exam_code": elem_code, "categories": elem_cats}

        # ── 高考三級 + 普考 ──
        hg_code = f"{year}080"
        log.info(f"\n掃描 {year} 年高考三級 ({hg_code})...")
        senior_cats = self._scan_categories(hg_code, CATEGORY_RANGES["senior"])

        log.info(f"掃描 {year} 年普考 ({hg_code})...")
        junior_cats = self._scan_categories(hg_code, CATEGORY_RANGES["junior"])

        if senior_cats or junior_cats:
            results["senior_junior"] = {
                "exam_code": hg_code,
                "senior": senior_cats,
                "junior": junior_cats,
            }

        return results

    def _scan_categories(
        self, exam_code: str, cat_codes: List[int]
    ) -> Dict[int, List[str]]:
        """掃描某個考試的所有類科，找出有選擇題的科目"""
        results = {}

        # 並行掃描所有類科
        futures = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for cat_code in cat_codes:
                future = executor.submit(
                    self._scan_category, exam_code, cat_code
                )
                futures[future] = cat_code

            for future in as_completed(futures):
                cat_code = futures[future]
                try:
                    subjects = future.result()
                    if subjects:
                        results[cat_code] = subjects
                        log.debug(f"  類科 {cat_code}: {len(subjects)} 個科目")
                except Exception as e:
                    log.warning(f"掃描類科 {cat_code} 失敗: {e}")

        return results

    def _scan_category(self, exam_code: str, cat_code: int) -> List[str]:
        """掃描某個類科，找出有選擇題（有答案）的科目"""
        subjects = []

        for sub_code in POSSIBLE_SUBJECTS:
            if self.check_subject_exists(exam_code, cat_code, sub_code):
                subjects.append(sub_code)

        return subjects


# ── 輸出 ────────────────────────────────────────────────────────────────

def results_to_yaml(results: Dict[int, Dict]) -> str:
    """將掃描結果轉換為 YAML 格式"""
    yaml_dict = {}

    for year, year_data in sorted(results.items()):
        # 初等考試
        if "elementary" in year_data:
            elem = year_data["elementary"]
            yaml_dict[elem["exam_code"]] = {
                str(cat_code): subjects
                for cat_code, subjects in sorted(elem["categories"].items())
            }

        # 高考 + 普考
        if "senior_junior" in year_data:
            sj = year_data["senior_junior"]
            yaml_dict[sj["exam_code"]] = {}

            # 高考（201-300）
            for cat_code, subjects in sorted(sj["senior"].items()):
                yaml_dict[sj["exam_code"]][str(cat_code)] = subjects

            # 普考（401-455）
            for cat_code, subjects in sorted(sj["junior"].items()):
                yaml_dict[sj["exam_code"]][str(cat_code)] = subjects

    # 轉換為 YAML 字串
    yaml_str = "# 自動生成的高普考題庫目錄\n"
    yaml_str += "# 生成時間：" + time.strftime("%Y-%m-%d %H:%M:%S") + "\n"
    yaml_str += "# 每個考試代碼下列出所有有選擇題的類科及其科目代碼\n\n"

    for exam_code in sorted(yaml_dict.keys()):
        yaml_str += f'"{exam_code}":\n'
        for cat_code in sorted(yaml_dict[exam_code].keys()):
            subjects = yaml_dict[exam_code][cat_code]
            yaml_str += f'  "{cat_code}":\n'
            for sub in sorted(subjects):
                yaml_str += f'    - "{sub}"\n'
        yaml_str += "\n"

    return yaml_str


# ── 主程式 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="自動生成高普考題庫 Catalog（年份+類科+科目）"
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[112, 113, 114],
        help="民國年份（預設：112 113 114）",
    )
    parser.add_argument(
        "--output",
        default="exam_catalog_complete.yaml",
        help="輸出 YAML 檔案名稱",
    )
    parser.add_argument(
        "--workers", type=int, default=8, help="並行掃描的執行緒數"
    )
    parser.add_argument(
        "--delay", type=float, default=0.3, help="請求之間的延遲秒數"
    )
    args = parser.parse_args()

    log.info(f"掃描年份：{args.years}")
    log.info(f"並行執行緒：{args.workers}")
    log.info(f"請求延遲：{args.delay} 秒")
    log.info(f"預期耗時：~{len(args.years) * 1500 * args.delay / 60:.1f} 分鐘")

    prober = Prober(max_workers=args.workers, request_delay=args.delay)
    all_results = {}

    for year in sorted(args.years):
        year_results = prober.scan_exam_year(year)
        all_results[year] = year_results

        # 統計
        elem_count = (
            sum(len(cats) for cats in year_results.get("elementary", {}).get("categories", {}).values())
            if "elementary" in year_results
            else 0
        )
        sj_count = sum(
            sum(len(cats) for cats in d.values())
            for d in [
                year_results.get("senior_junior", {}).get("senior", {}),
                year_results.get("senior_junior", {}).get("junior", {}),
            ]
        )
        log.info(f"✓ {year} 年：{elem_count + sj_count} 個科目")

    # 輸出 YAML
    yaml_content = results_to_yaml(all_results)
    output_file = Path(__file__).resolve().parent / args.output

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    log.info(f"\n✓ Catalog 已保存至：{output_file}")
    log.info(f"  使用方式：python moex_simple.py all --config {args.output}")

    # 摘要
    log.info("\n" + "="*60)
    log.info("掃描摘要")
    log.info("="*60)
    for year in sorted(all_results.keys()):
        year_data = all_results[year]
        if "elementary" in year_data:
            elem_cats = year_data["elementary"]["categories"]
            log.info(f"{year} 年初等：{len(elem_cats)} 類科")
        if "senior_junior" in year_data:
            sj = year_data["senior_junior"]
            log.info(
                f"{year} 年高普考：{len(sj['senior'])} 類高考 + {len(sj['junior'])} 類普考"
            )


if __name__ == "__main__":
    main()
