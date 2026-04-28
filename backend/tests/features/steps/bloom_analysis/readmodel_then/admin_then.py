"""Then 步驟 — 管理員 Bloom 分類匯入結果。"""

from behave import then


@then('系統應呼叫 AI 分類服務，為每道題目填入 bloom_category')
def step_then_ai_called(context):
    assert context.memo.get("admin_ai_called"), "AI 分類服務未被呼叫"
    classified = context.memo.get("admin_classified_questions") or []
    assert classified, "未取得分類後題目"
    for q in classified:
        assert q.get("bloom_category"), (
            f"題 {q.get('question_number')} 的 bloom_category 未被填入"
        )


@then('{count:d} 題處理完成後，匯入結果應顯示各 Bloom 分類統計')
def step_then_classification_stats(context, count):
    classified = context.memo.get("admin_classified_questions") or []
    assert len(classified) == count, (
        f"處理題數應為 {count}，實得 {len(classified)}"
    )
    counts = context.memo.get("admin_classification_counts") or {}
    assert counts, "未產生分類統計"
    assert sum(counts.values()) == count, (
        f"統計總和 {sum(counts.values())} ≠ {count}"
    )
    # 至少 3 個 Bloom 類別有被使用（cycle 50/6 ≈ 8 each）
    non_zero = [k for k, v in counts.items() if v > 0]
    assert len(non_zero) >= 3, f"分類過於集中：{counts}"
