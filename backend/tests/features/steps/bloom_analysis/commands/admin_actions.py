"""When 管理員觸發 Bloom 分類 / 匯入（B-route：尚無 endpoint，模擬服務行為）。"""

from behave import when

from app.models.question import BloomCategory


_BLOOM_CYCLE = list(BloomCategory)


@when('管理員觸發「自動 Bloom 分類」')
def step_admin_trigger_bloom_classification(context):
    questions = context.memo.get("admin_uploaded_questions") or []
    classified = []
    counts = {b.value: 0 for b in BloomCategory}
    for i, q in enumerate(questions):
        # 模擬 AI 分類：cycle through 6 個 Bloom 類別
        cat = _BLOOM_CYCLE[i % len(_BLOOM_CYCLE)].value
        new_q = dict(q)
        new_q["bloom_category"] = cat
        counts[cat] += 1
        classified.append(new_q)
    context.memo["admin_classified_questions"] = classified
    context.memo["admin_classification_counts"] = counts
    context.memo["admin_ai_called"] = True
    # 清掉 last_response，讓 Then 走 unit-test 模式
    context.last_response = None
    context.last_error = None


@when('管理員觸發匯入')
def step_admin_trigger_import(context):
    questions = context.memo.get("admin_uploaded_invalid_questions") or []
    context.last_response = None
    context.last_error = None
    for q in questions:
        if "correct_answer" not in q or q.get("correct_answer") in (None, ""):
            context.last_error = (
                f"第 {q['question_number']} 題缺少必填欄位：correct_answer"
            )
            return
    # 若全部欄位齊全，視為匯入成功（此 scenario 不會走到此分支）
    context.memo["admin_import_ok"] = True
