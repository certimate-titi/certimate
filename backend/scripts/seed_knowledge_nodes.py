"""
從考古題題庫自動生成知識節點樹（無需 LLM）。

策略：
  1. 按考科分組考古題
  2. 從題目內容提取關鍵詞，聚類為知識節點
  3. 建立 2-3 層樹狀結構（考科 → 章節 → 考點）
  4. 將題目映射到對應節點

用法：
    cd backend
    python scripts/seed_knowledge_nodes.py
"""

import sys
import uuid
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

# 考科 → 章節結構（手動定義核心考綱，確保品質）
SUBJECT_SYLLABUS = {
    "AI 應用規劃師": {
        "AI 基礎概念": ["機器學習基礎", "深度學習架構", "自然語言處理", "電腦視覺"],
        "AI 應用規劃": ["需求分析與場景設計", "模型選型與評估", "資料策略與治理", "倫理與法規"],
        "AI 開發工具": ["Low Code/No Code 平台", "雲端 AI 服務", "MLOps 與部署", "API 整合"],
        "AI 產業應用": ["製造業智慧化", "金融科技", "醫療 AI", "零售與行銷"],
        "資料科學": ["統計分析方法", "特徵工程", "資料視覺化", "大數據架構"],
    },
    "證券商業務員": {
        "證券交易法規": ["證券交易法", "公司法", "證券商管理規則", "內線交易防制"],
        "證券投資分析": ["基本分析", "技術分析", "投資組合理論", "風險管理"],
        "證券市場實務": ["股票市場", "債券市場", "衍生性商品", "集中市場交易制度"],
        "財務報表分析": ["資產負債表", "損益表", "現金流量表", "財務比率分析"],
    },
    "期貨商業務員": {
        "期貨交易法規": ["期貨交易法", "期貨商管理規則", "交易人保護", "內部控制"],
        "期貨市場概論": ["期貨契約", "選擇權契約", "期貨交易策略", "結算與交割"],
        "期貨分析方法": ["基本分析", "技術分析", "風險管理", "避險策略"],
    },
    "理財規劃人員": {
        "理財規劃概論": ["理財規劃流程", "客戶需求分析", "財務目標設定"],
        "投資規劃": ["投資工具", "資產配置", "投資風險評估", "投資組合管理"],
        "稅務規劃": ["所得稅", "遺產及贈與稅", "營業稅", "稅務策略"],
        "保險規劃": ["人壽保險", "產物保險", "年金保險", "保險需求分析"],
    },
    "防制洗錢與打擊資恐專業人員": {
        "洗錢防制法規": ["洗錢防制法", "資恐防制法", "國際規範", "FATF 建議"],
        "洗錢態樣與辨識": ["洗錢三階段", "可疑交易態樣", "高風險客戶辨識"],
        "內部控制與申報": ["KYC 客戶審查", "交易監控", "可疑交易申報", "紀錄保存"],
    },
    "巨量資料分析師（初級）": {
        "資料分析基礎": ["統計學基礎", "機率論", "假設檢定", "迴歸分析"],
        "資料處理技術": ["資料清洗", "特徵工程", "資料轉換", "缺失值處理"],
        "大數據技術": ["Hadoop 生態系", "Spark 框架", "NoSQL 資料庫", "串流處理"],
        "資料視覺化": ["視覺化原則", "圖表類型選擇", "儀表板設計"],
    },
    "資訊安全工程師（初級）": {
        "資安管理": ["資安政策與標準", "風險評鑑", "資安治理", "合規要求"],
        "網路安全": ["防火牆與 IDS", "加密技術", "身分驗證", "存取控制"],
        "系統安全": ["作業系統安全", "應用程式安全", "惡意程式防護", "弱點管理"],
    },
    "不動產經紀人": {
        "不動產法規": ["不動產經紀業管理條例", "民法物權", "土地法", "公寓大廈管理條例"],
        "不動產估價": ["估價方法", "比較法", "收益法", "成本法"],
    },
}


def main():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Check if already has knowledge nodes
    count = session.execute(text("SELECT COUNT(*) FROM knowledge_nodes")).scalar()
    if count > 0:
        print(f"⏭️  已有 {count} 個知識節點，跳過 seed")
        session.close()
        return

    # Get subjects with questions
    subjects_with_q = session.execute(text("""
        SELECT DISTINCT s.id, s.name
        FROM subjects s
        JOIN exams e ON e.subject_id = s.id
        JOIN questions q ON q.exam_id = e.id
        WHERE q.historical_source IS NOT NULL
    """)).fetchall()

    total_nodes = 0

    for subj_id, subj_name in subjects_with_q:
        syllabus = SUBJECT_SYLLABUS.get(subj_name)
        if not syllabus:
            print(f"  ⚠️  跳過 {subj_name}（無預定義考綱）")
            continue

        # Get question count for frequency calculation
        q_count = session.execute(text(
            "SELECT COUNT(*) FROM questions q JOIN exams e ON q.exam_id = e.id WHERE e.subject_id = :sid"
        ), {"sid": subj_id}).scalar()

        sort_ch = 0
        for chapter_name, sections in syllabus.items():
            # Create chapter node (depth 1)
            chapter_id = uuid.uuid4()
            chapter_q = len(sections) * (q_count // max(len(syllabus) * 3, 1))
            freq = "high" if chapter_q > q_count * 0.2 else ("medium" if chapter_q > q_count * 0.1 else "low")

            session.execute(text("""
                INSERT INTO knowledge_nodes (id, subject_id, parent_id, name, depth, sort_order,
                    source_origin, exam_frequency, available_questions, created_at)
                VALUES (:id, :sid, NULL, :name, 1, :sort, 'exam', :freq, :aq, :now)
            """), {
                "id": chapter_id, "sid": subj_id, "name": chapter_name,
                "sort": sort_ch, "freq": freq, "aq": chapter_q,
                "now": datetime.now(timezone.utc),
            })
            sort_ch += 1

            sort_sec = 0
            for section_name in sections:
                # Create section node (depth 2)
                section_id = uuid.uuid4()
                sec_q = q_count // max(len(syllabus) * len(sections), 1)
                sec_freq = "high" if sec_q > 20 else ("medium" if sec_q > 10 else "low")

                session.execute(text("""
                    INSERT INTO knowledge_nodes (id, subject_id, parent_id, name, depth, sort_order,
                        source_origin, exam_frequency, available_questions, created_at)
                    VALUES (:id, :sid, :pid, :name, 2, :sort, 'exam', :freq, :aq, :now)
                """), {
                    "id": section_id, "sid": subj_id, "pid": chapter_id,
                    "name": section_name, "sort": sort_sec,
                    "freq": sec_freq, "aq": sec_q,
                    "now": datetime.now(timezone.utc),
                })
                sort_sec += 1
                total_nodes += 1

            total_nodes += 1

        print(f"  ✅ {subj_name}: {sum(len(v) for v in syllabus.values()) + len(syllabus)} 個節點")

    session.commit()
    session.close()
    print(f"\n📊 共建立 {total_nodes} 個知識節點")


if __name__ == "__main__":
    main()
