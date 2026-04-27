#!/usr/bin/env python3
"""考古題 Bloom 認知層次 AI 批次分類.

使用 Gemini Flash 為已匯入的考古題進行 Bloom 分類。

使用方式：
    # Dry-run（僅顯示分類結果，不寫入 DB）
    .venv/bin/python -m app.scripts.bloom_classifier --dry-run --limit 10

    # 正式執行（預設每批 20 題）
    .venv/bin/python -m app.scripts.bloom_classifier

    # 指定考試代碼
    .venv/bin/python -m app.scripts.bloom_classifier --exam-code 114010

環境變數：
    GEMINI_API_KEY — Google Gemini API Key
"""

import argparse
import json
import logging
import os
import time

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.question import Question

settings = get_settings()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BLOOM_LEVELS = {"remember", "understand", "apply", "analyze", "evaluate", "create"}

CLASSIFICATION_PROMPT = """你是一位教育評量專家。請分析以下考試題目，判斷其 Bloom 認知層次。

題目：{content}
選項：
A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}

Bloom 認知層次定義：
- remember（記憶）：回想特定知識、事實、術語
- understand（理解）：解釋、詮釋、摘要概念
- apply（應用）：將知識用於具體情境或問題
- analyze（分析）：拆解、比較、找出因果關聯
- evaluate（評估）：評判、做出有根據的決策
- create（創造）：整合知識提出新方案或設計

請只回傳一個英文分類名稱（如 remember），不要附加任何說明。"""


def classify_batch_gemini(questions: list[dict], api_key: str) -> list[str]:
    """使用 Gemini API 對一批考題進行 Bloom 認知層次分類。

    Args:
        questions: 題目 dict 串列，每筆需包含 ``content`` / ``option_a`` ~
            ``option_d`` 欄位。
        api_key: Google Gemini API 金鑰。

    Returns:
        對應每題的 Bloom 層次串列（``remember`` / ``understand`` / ``apply``
        / ``analyze`` / ``evaluate`` / ``create``）；API 失敗或回傳值不在合
        法集合時 fallback 為 ``remember``。

    Notes:
        每呼叫 1 次 ``generate_content`` 後 ``time.sleep(0.1)`` 以避免觸發
        Gemini Rate Limit。
    """
    try:
        from google import genai
    except ImportError:
        log.error("需要 google-genai：pip install google-genai")
        return ["remember"] * len(questions)

    client = genai.Client(api_key=api_key)

    results = []
    for q in questions:
        prompt = CLASSIFICATION_PROMPT.format(
            content=q.get("content", ""),
            option_a=q.get("option_a", ""),
            option_b=q.get("option_b", ""),
            option_c=q.get("option_c", ""),
            option_d=q.get("option_d", ""),
        )
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            bloom = response.text.strip().lower()
            if bloom not in BLOOM_LEVELS:
                # 嘗試提取第一個有效值
                for level in BLOOM_LEVELS:
                    if level in bloom:
                        bloom = level
                        break
                else:
                    bloom = "remember"  # fallback
            results.append(bloom)
        except Exception as e:
            log.warning(f"Gemini API 失敗: {e}")
            results.append("remember")
        time.sleep(0.1)  # Rate limit

    return results


def classify_batch_heuristic(questions: list[dict]) -> list[str]:
    """以中文關鍵字啟發式判斷 Bloom 認知層次（無需 API key）。

    Args:
        questions: 題目 dict 串列，僅讀取 ``content`` 欄位。

    Returns:
        對應每題的 Bloom 層次串列；無關鍵字命中時 fallback 為 ``remember``。
    """
    results = []
    for q in questions:
        content = (q.get("content", "") or "").lower()
        # 關鍵字啟發式
        if any(kw in content for kw in ["何者為", "下列何者", "所謂", "係指", "定義"]):
            results.append("remember")
        elif any(kw in content for kw in ["說明", "解釋", "意義", "何意", "為何"]):
            results.append("understand")
        elif any(kw in content for kw in ["如何", "計算", "應如何", "依據", "處理"]):
            results.append("apply")
        elif any(kw in content for kw in ["比較", "差異", "關係", "原因", "影響"]):
            results.append("analyze")
        elif any(kw in content for kw in ["最適", "最佳", "應優先", "評估", "判斷"]):
            results.append("evaluate")
        elif any(kw in content for kw in ["設計", "規劃", "提出", "建議", "方案"]):
            results.append("create")
        else:
            results.append("remember")
    return results


def main():
    """CLI 進入點：批次為考古題填入 ``bloom_category``。

    流程：
        1. 連線資料庫並查詢尚未分類（``bloom_category IS NULL``）的考古題。
        2. 依 ``--batch-size`` 分批，依 ``--use-ai`` 決定走 Gemini 或啟發式
           分類器。
        3. 將分類結果寫回 ``questions.bloom_category``，``--dry-run`` 模式
           則 rollback。

    副作用：
        於非 dry-run 模式下會 ``UPDATE questions`` 寫入 Bloom 分類，並輸出
        各層次分佈統計到 log。
    """
    parser = argparse.ArgumentParser(description="考古題 Bloom 認知層次 AI 批次分類")
    parser.add_argument("--dry-run", action="store_true", help="不寫入 DB")
    parser.add_argument("--limit", type=int, default=0, help="處理題數上限（0=全部）")
    parser.add_argument("--batch-size", type=int, default=20, help="每批題數")
    parser.add_argument("--exam-code", help="僅處理指定考試代碼")
    parser.add_argument("--use-ai", action="store_true", help="使用 Gemini AI（需 GEMINI_API_KEY）")
    args = parser.parse_args()

    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    # 查詢未分類的考古題
    query = db.query(Question).filter(
        Question.historical_exam_id.isnot(None),
        Question.bloom_category.is_(None),
    )

    if args.exam_code:
        from app.models.historical_exam import HistoricalExam
        query = query.join(HistoricalExam).filter(HistoricalExam.exam_code == args.exam_code)

    total = query.count()
    log.info(f"待分類題目: {total}")

    if args.limit:
        questions = query.limit(args.limit).all()
    else:
        questions = query.all()

    log.info(f"本次處理: {len(questions)} 題")

    api_key = os.environ.get("GEMINI_API_KEY", "")
    classified = 0
    distribution = {level: 0 for level in BLOOM_LEVELS}

    for i in range(0, len(questions), args.batch_size):
        batch = questions[i:i + args.batch_size]
        batch_data = [
            {
                "content": q.content,
                "option_a": q.option_a or "",
                "option_b": q.option_b or "",
                "option_c": q.option_c or "",
                "option_d": q.option_d or "",
            }
            for q in batch
        ]

        if args.use_ai and api_key:
            blooms = classify_batch_gemini(batch_data, api_key)
        else:
            blooms = classify_batch_heuristic(batch_data)

        for q, bloom in zip(batch, blooms):
            q.bloom_category = bloom
            distribution[bloom] += 1
            classified += 1

        if not args.dry_run:
            db.commit()

        log.info(f"  批次 {i // args.batch_size + 1}: {len(batch)} 題")

    log.info(f"\n分類完成: {classified} 題")
    log.info(f"Bloom 分佈:")
    for level, count in sorted(distribution.items(), key=lambda x: -x[1]):
        pct = count / max(1, classified) * 100
        log.info(f"  {level:12s}: {count:5d} ({pct:.1f}%)")

    if args.dry_run:
        log.info("\n🔍 dry-run — 未寫入 DB")
        db.rollback()
    else:
        log.info("\n✅ 已寫入 DB")

    db.close()


if __name__ == "__main__":
    main()
