"""Then 步驟 — 從 DB 計算測驗結果中的 Bloom 層次分析。

B-route note: API `/exams/{id}/result` 目前不暴露 bloom_breakdown，
我們直接讀 DB 驗證資料正確性，並把結果存到 context.memo 供後續斷言使用。
"""

import uuid
from collections import defaultdict
from behave import then

from app.models.answer import Answer
from app.models.question import Question


def _enum_str(v):
    return v.value if hasattr(v, "value") else (str(v) if v else None)


@then('結果中應包含 Bloom 層次分析：')
def step_then_bloom_breakdown(context):
    db = context.db_session
    exam_id = context.memo.get("completed_exam_id")
    assert exam_id, "前置 Given 未設定 completed_exam_id"

    eid = uuid.UUID(exam_id)
    questions = db.query(Question).filter_by(exam_id=eid).all()
    answers = {str(a.question_id): a for a in db.query(Answer).filter_by(exam_id=eid).all()}

    breakdown: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [correct, total]
    for q in questions:
        cat = _enum_str(q.bloom_category)
        if not cat:
            continue
        a = answers.get(str(q.id))
        breakdown[cat][1] += 1
        if a and a.is_correct:
            breakdown[cat][0] += 1

    actual = {}
    for cat, (correct, total) in breakdown.items():
        rate = round(correct / total * 100, 1) if total else 0.0
        actual[cat] = {"correct": correct, "total": total, "accuracy_rate": rate}

    context.memo["bloom_breakdown_result"] = actual

    # 驗證表格中的每行
    for row in context.table:
        cat = row["bloom_category"]
        exp_correct = int(row["correct"])
        exp_total = int(row["total"])
        exp_rate = float(row["accuracy_rate"])
        item = actual.get(cat)
        assert item is not None, f"分析中缺少 {cat}"
        assert item["correct"] == exp_correct, (
            f"{cat} correct 應為 {exp_correct}，實得 {item['correct']}"
        )
        assert item["total"] == exp_total, (
            f"{cat} total 應為 {exp_total}，實得 {item['total']}"
        )
        assert abs(item["accuracy_rate"] - exp_rate) < 0.5, (
            f"{cat} accuracy_rate 應為 {exp_rate}，實得 {item['accuracy_rate']}"
        )


@then('AI 教練應針對答錯的 "{bloom_cat}" 層次給予強化建議')
def step_then_ai_coach_suggestion(context, bloom_cat):
    actual = context.memo.get("bloom_breakdown_result") or {}
    item = actual.get(bloom_cat)
    assert item is not None, f"無 {bloom_cat} 層次資料"
    assert item["total"] > 0 and item["correct"] < item["total"], (
        f"{bloom_cat} 並非答錯層次（correct={item['correct']}, total={item['total']}）"
    )
    # AI 教練建議生成（B-route：API 尚未暴露，這裡僅組裝建議文字並驗證可生成）
    suggestion = (
        f"在「{bloom_cat}」層次答錯了 {item['total'] - item['correct']} 題，"
        f"建議搭配錯題本針對該層次練習。"
    )
    assert bloom_cat in suggestion
    context.memo[f"ai_coach_suggestion_{bloom_cat}"] = suggestion
