"""
簡化版：基於已知的類科代碼，嘗試下載所有選擇題科目
直接進行 download + parse 階段
"""

import json
import sys
from pathlib import Path
import requests
import time
import urllib3

urllib3.disable_warnings()

# 已知的 MC 科目代碼組合（根據初步掃描）
# 以 (exam_code, category_code, subject_code) 為單位
KNOWN_MC_SUBJECTS = [
    # 114 年初等考試
    ("114010", "501", "0101"),  # 初等_一般行政_國文
    ("114010", "501", "0102"),  # 初等_一般行政_公民與英文
    ("114010", "501", "0501"),  # 初等_一般行政_管理概要
    ("114010", "501", "0502"),  # 初等_一般行政_法律常識
]

DOWNLOAD_URL = "https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx"
PDF_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "historical_questions" / "_pdf"

session = requests.Session()
session.verify = False


def download_pdf(exam_code, cat_code, sub_code, file_type="Q"):
    """下載單個 PDF"""
    params = {
        "t": file_type,
        "code": exam_code,
        "c": cat_code,
        "s": sub_code,
        "q": "1",
    }
    try:
        resp = session.get(DOWNLOAD_URL, params=params, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 300:
            return resp.content
    except Exception as e:
        print(f"下載失敗: {e}")
    return None


def download_all():
    """下載所有已知的 MC 科目 PDF"""
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    total = len(KNOWN_MC_SUBJECTS)
    for idx, (exam_code, cat_code, sub_code) in enumerate(KNOWN_MC_SUBJECTS, 1):
        print(f"\n[{idx}/{total}] 下載 {exam_code}/{cat_code}/{sub_code}")

        # 試題 PDF
        q_data = download_pdf(exam_code, cat_code, sub_code, "Q")
        if q_data:
            q_file = PDF_DIR / f"Q_{exam_code}_{cat_code}_{sub_code}.pdf"
            q_file.write_bytes(q_data)
            print(f"  ✓ 試題 {len(q_data)} bytes")
        else:
            print(f"  ✗ 試題下載失敗")
            continue

        # 答案 PDF
        s_data = download_pdf(exam_code, cat_code, sub_code, "S")
        if s_data:
            s_file = PDF_DIR / f"S_{exam_code}_{cat_code}_{sub_code}.pdf"
            s_file.write_bytes(s_data)
            print(f"  ✓ 答案 {len(s_data)} bytes")
        else:
            print(f"  ✗ 答案下載失敗")

        time.sleep(1)

    print(f"\n下載完成！PDF 儲存於 {PDF_DIR}")


if __name__ == "__main__":
    download_all()
