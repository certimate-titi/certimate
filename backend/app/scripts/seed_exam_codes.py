"""
啟動時自動 Seed exam_subject_codes（冪等操作）。

每次部署後 exam_subject_codes 可能為空，此腳本確保資料正確。
由 entrypoint.sh 在啟動時呼叫。
"""

import logging

log = logging.getLogger(__name__)

CODES = {
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


def seed_exam_codes() -> str:
    """Seed exam_subject_codes for all known subjects. Idempotent."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.config import get_settings
    from app.models.subject import Subject

    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        updated = 0
        skipped = 0
        for name, codes in CODES.items():
            subject = db.query(Subject).filter_by(name=name).first()
            if subject:
                if subject.exam_subject_codes == codes:
                    skipped += 1
                    continue
                subject.exam_subject_codes = codes
                updated += 1
            else:
                log.warning(f"Subject not found: {name}")
        db.commit()
        return f"updated={updated}, skipped={skipped} (already correct)"
    except Exception as e:
        db.rollback()
        log.error(f"Seed exam_subject_codes failed: {e}")
        return f"error: {e}"
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = seed_exam_codes()
    print(result)
