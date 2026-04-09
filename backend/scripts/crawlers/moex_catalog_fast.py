"""
快速目錄生成：使用已知的類科代碼清單 + 并行掃描
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import urllib3

urllib3.disable_warnings()

# 已知的類科代碼（根據考選部研究結果）
KNOWN_CATEGORIES = {
    "elementary": list(range(501, 517)),   # 初等：501-516
    "junior": list(range(401, 456)),       # 普考：401-455
    "senior": list(range(201, 301)),       # 高考：201-300
}

# 常見科目代碼
SUBJECT_CODES = [
    "0101", "0102",  # 國文
    "0401", "0402",  # 法學知識與英文
    "0301", "0302", "0303", "0304", "0305", "0306",  # 專業科目 1-6
    "0403", "0404", "0405", "0406", "0407", "0408",  # 其他專業科目
]

DOWNLOAD_URL = "https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx"


def check_subject_has_answer(exam_code, cat_code, sub_code):
    """檢查某科目是否有標準答案（選擇題指標）"""
    s = requests.Session()
    s.verify = False
    try:
        resp = s.get(
            DOWNLOAD_URL,
            params={"t": "S", "code": exam_code, "c": str(cat_code), "s": sub_code, "q": "1"},
            timeout=10,
        )
        return resp.status_code == 200 and len(resp.content) > 300
    except Exception:
        return False


def scan_exam_year(year):
    """掃描某一年的所有考試"""
    results = {}

    # 初等考試
    exam_code = f"{year}010"
    print(f"\n掃描 {year} 年初等考試 ({exam_code})...")
    elem_cats = {}
    for cat_code in KNOWN_CATEGORIES["elementary"]:
        mc_subs = []
        for sub_code in SUBJECT_CODES:
            if check_subject_has_answer(exam_code, cat_code, sub_code):
                mc_subs.append(sub_code)
        if mc_subs:
            elem_cats[str(cat_code)] = mc_subs
            print(f"  類科 {cat_code}: {len(mc_subs)} 個選擇題")
        time.sleep(0.1)

    if elem_cats:
        results["elementary"] = {"code": exam_code, "categories": elem_cats}

    # 高考三級 + 普考
    exam_code = f"{year}080"
    print(f"\n掃描 {year} 年高考 + 普考 ({exam_code})...")

    senior_cats = {}
    for cat_code in KNOWN_CATEGORIES["senior"]:
        mc_subs = []
        for sub_code in SUBJECT_CODES:
            if check_subject_has_answer(exam_code, cat_code, sub_code):
                mc_subs.append(sub_code)
        if mc_subs:
            senior_cats[str(cat_code)] = mc_subs
        time.sleep(0.05)

    junior_cats = {}
    for cat_code in KNOWN_CATEGORIES["junior"]:
        mc_subs = []
        for sub_code in SUBJECT_CODES:
            if check_subject_has_answer(exam_code, cat_code, sub_code):
                mc_subs.append(sub_code)
        if mc_subs:
            junior_cats[str(cat_code)] = mc_subs
        time.sleep(0.05)

    if senior_cats or junior_cats:
        results["senior_junior"] = {
            "code": exam_code,
            "senior": senior_cats,
            "junior": junior_cats,
        }
        print(f"  高考: {len(senior_cats)} 類科, 普考: {len(junior_cats)} 類科")

    return results


if __name__ == "__main__":
    print("開始掃描 112-114 年考試...")
    all_results = {}

    for year in [112, 113, 114]:
        all_results[year] = scan_exam_year(year)
        time.sleep(1)

    # 儲存
    with open("/Users/simon/certimate/project/backend/data/historical_questions/_catalog/catalog_fast_114-114.json",
              "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print("\n完成！")
    print(json.dumps(all_results, ensure_ascii=False, indent=2))
