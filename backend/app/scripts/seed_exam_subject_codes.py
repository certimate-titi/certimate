#!/usr/bin/env python3
"""
填入 subjects.exam_subject_codes 映射 + 新增高普考類科。

格式：["exam_code:subject_code", ...]
例：["114080:0102", "114080:0402", "114080:0302", "114080:0304", "114080:0406"]

使用方式：
    .venv/bin/python -m app.scripts.seed_exam_subject_codes --dry-run   # 預覽
    .venv/bin/python -m app.scripts.seed_exam_subject_codes             # 執行
"""

import argparse
import logging
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.subject import Subject, SubjectCategory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CIVIL_SERVICE_CATEGORY_ID = "a0000001-0000-0000-0000-000000000007"  # 公務員
FINANCE_CATEGORY_ID = "a0000001-0000-0000-0000-000000000001"  # 金融
IT_CATEGORY_ID = "a0000001-0000-0000-0000-000000000004"  # IT

# ── 現有科目的 exam_subject_codes ──────────────────────────────

EXISTING_SUBJECT_CODES = {
    "AI 應用規劃師（初級）": [
        "IPA114:114_ai_fundamentals_4th",
        "IPA114:114_ai_application_4th",
    ],
    "AI 應用規劃師（中級）": [
        "IPA114:114_ai_mid_ml",
        "IPA114:114_ai_mid_bigdata",
        "IPA114:114_ai_mid_tech_planning",
    ],
    "證券商業務員": [
        "FIN114:securities_salesperson_session01_questions",
        "FIN114:securities_salesperson_session02_questions",
        "FIN114:senior_securities_session01_questions",
        "FIN114:senior_securities_session02_questions",
        "FIN114:securities_regulations_b_session01_questions",
        "FIN114:securities_regulations_b_session02_questions",
        "FIN114:internal_control_session01_questions",
        "FIN114:internal_control_session02_questions",
    ],
    "期貨商業務員": [
        "FIN114:futures_salesperson_session01_questions",
        "FIN114:futures_salesperson_session02_questions",
        "FIN114:futures_analyst_session01_questions",
        "FIN114:futures_analyst_session02_questions",
        "FIN114:futures_trust_fund_session01_questions",
        "FIN114:futures_trust_fund_session02_questions",
    ],
    "理財規劃人員": [
        "FIN114:investment_trust_session01_questions",
        "FIN114:investment_trust_session02_questions",
        "FIN114:investment_regulations_b_session01_questions",
        "FIN114:investment_regulations_b_session02_questions",
    ],
    "防制洗錢與打擊資恐專業人員": [
        "FIN114:aml_cft_session01_questions",
        "FIN114:aml_cft_session02_questions",
        "FIN114:sustainability_session01_questions",
        "FIN114:sustainability_session02_questions",
    ],
    "資訊安全工程師（初級）": [
        "IPA114:114_is_beginner_management",
        "IPA114:114_is_beginner_tech",
    ],
    "巨量資料分析師（初級）": [
        "IPA111:111_bda_beginner_subject1",
        "IPA111:111_bda_beginner_subject2",
        "IPA109:109_bda_beginner_sample_subject1",
        "IPA109:109_bda_beginner_sample_subject2",
    ],
    "不動產經紀人": [
        "REA111:111_land_law_q",
        "REA111:111_broker_regulations_q",
        "REA111:111_civil_law_q",
        "REA111:111_valuation_q",
        "REA112:112_land_law_q",
        "REA112:112_broker_regulations_q",
        "REA112:112_civil_law_q",
        "REA112:112_valuation_q",
    ],
}

# ── 高普考新增科目 ──────────────────────────────────────────────

# 114年初等考試類科
ELEMENTARY_SUBJECTS = {
    "一般行政（初等）": {
        "codes": ["114010:0101", "114010:0102", "114010:0202", "114010:0302"],
        "id": "c0000001-0501-0000-0000-000000000001",
    },
    "社會行政（初等）": {
        "codes": ["114010:0101", "114010:0102", "114010:0202", "114010:0303"],
        "id": "c0000001-0502-0000-0000-000000000001",
    },
    "人事行政（初等）": {
        "codes": ["114010:0101", "114010:0102", "114010:0202", "114010:0203"],
        "id": "c0000001-0503-0000-0000-000000000001",
    },
    "教育行政（初等）": {
        "codes": ["114010:0101", "114010:0102", "114010:0301", "114010:0304"],
        "id": "c0000001-0504-0000-0000-000000000001",
    },
    "財稅行政（初等）": {
        "codes": ["114010:0101", "114010:0102", "114010:0401", "114010:0404"],
        "id": "c0000001-0505-0000-0000-000000000001",
    },
}

# 114年普通考試類科
REGULAR_SUBJECTS = {
    "一般行政（普考）": {
        "codes": ["114080:0102", "114080:0402", "114080:0302", "114080:0304", "114080:0406"],
        "id": "c0000002-0401-0000-0000-000000000001",
    },
    "一般民政（普考）": {
        "codes": ["114080:0102", "114080:0402", "114080:0304", "114080:0307", "114080:0406"],
        "id": "c0000002-0402-0000-0000-000000000001",
    },
    "人事行政（普考）": {
        "codes": ["114080:0102", "114080:0402", "114080:0304", "114080:0406"],
        "id": "c0000002-0412-0000-0000-000000000001",
    },
    "財稅行政（普考）": {
        "codes": ["114080:0102", "114080:0402", "114080:0406"],
        "id": "c0000002-0405-0000-0000-000000000001",
    },
    "會計（普考）": {
        "codes": ["114080:0102", "114080:0402", "114080:0406"],
        "id": "c0000002-0417-0000-0000-000000000001",
    },
}

# 114年高考三級類科
SENIOR_SUBJECTS = {
    "一般行政（高考）": {
        "codes": ["114080:0101", "114080:0401", "114080:0303", "114080:0403"],
        "id": "c0000003-0201-0000-0000-000000000001",
    },
    "一般民政（高考）": {
        "codes": ["114080:0101", "114080:0401", "114080:0303", "114080:0403"],
        "id": "c0000003-0202-0000-0000-000000000001",
    },
    "人事行政（高考）": {
        "codes": ["114080:0101", "114080:0401", "114080:0303", "114080:0403"],
        "id": "c0000003-0221-0000-0000-000000000001",
    },
}


def main():
    parser = argparse.ArgumentParser(description="Seed exam_subject_codes")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    engine = create_engine(get_settings().DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. 更新現有科目的 exam_subject_codes
        log.info("=== 更新現有科目 ===")
        for name, codes in EXISTING_SUBJECT_CODES.items():
            subject = db.query(Subject).filter(Subject.name == name).first()
            if subject:
                log.info(f"  {name}: {len(codes)} codes")
                if not args.dry_run:
                    subject.exam_subject_codes = codes
            else:
                log.warning(f"  {name}: 科目不存在，跳過")

        # 2. 新增高普考類科
        civil_service_cat_id = uuid.UUID(CIVIL_SERVICE_CATEGORY_ID)

        all_new = {}
        all_new.update(ELEMENTARY_SUBJECTS)
        all_new.update(REGULAR_SUBJECTS)
        all_new.update(SENIOR_SUBJECTS)

        log.info(f"\n=== 新增高普考類科 ({len(all_new)} 個) ===")
        created = 0
        skipped = 0
        for name, info in all_new.items():
            existing = db.query(Subject).filter(Subject.name == name).first()
            if existing:
                log.info(f"  {name}: 已存在，更新 codes")
                if not args.dry_run:
                    existing.exam_subject_codes = info["codes"]
                skipped += 1
            else:
                log.info(f"  {name}: 新增 ({len(info['codes'])} codes)")
                if not args.dry_run:
                    db.add(Subject(
                        id=uuid.UUID(info["id"]),
                        name=name,
                        category_id=civil_service_cat_id,
                        exam_subject_codes=info["codes"],
                        is_popular=False,
                    ))
                created += 1

        if not args.dry_run:
            db.commit()
            log.info(f"\n完成：新增 {created} 個科目，更新 {skipped} 個既有科目")
        else:
            log.info(f"\n[DRY-RUN] 將新增 {created} 個科目，更新 {skipped + len(EXISTING_SUBJECT_CODES)} 個既有科目")

    except Exception as e:
        db.rollback()
        log.error(f"錯誤：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
