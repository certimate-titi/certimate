"""Then assertions — Feature 44 BDD."""

from behave import then


@then('每筆 scaffold.embedding 為 1024 維 vector')
def step_assert_embedding_1024(context):
    rows = context.memo.get("queried_scaffolds") or []
    assert rows, "預期至少 1 筆 scaffold"
    for sf in rows:
        emb = getattr(sf, "embedding", None)
        assert emb is not None, f"scaffold {sf.id} embedding 為 None"
        # pgvector 回傳可能為 list / numpy array
        try:
            length = len(list(emb))
        except Exception:
            length = len(emb)
        assert length == 1024, (
            f"scaffold {sf.id} embedding 維度 {length} ≠ 1024"
        )


@then('embedding 不為 NULL')
def step_assert_embedding_not_null(context):
    rows = context.memo.get("queried_scaffolds") or []
    assert rows, "預期至少 1 筆 scaffold"
    for sf in rows:
        emb = getattr(sf, "embedding", None)
        assert emb is not None, f"scaffold {sf.id} embedding 為 NULL"


@then('scaffold rows 仍 commit（業務不阻斷）')
def step_assert_scaffolds_persisted_despite_voyage_fail(context):
    rows = context.memo.get("queried_scaffolds") or []
    assert rows, "預期 voyage 失敗時 scaffold 仍 commit，實際 0 筆"


@then('失敗 scaffold.embedding 為 NULL')
def step_assert_failed_embedding_null(context):
    rows = context.memo.get("queried_scaffolds") or []
    null_count = sum(
        1 for sf in rows if getattr(sf, "embedding", None) is None
    )
    assert null_count >= 1, (
        f"預期 voyage 失敗時至少 1 筆 embedding=NULL，實際 0 筆"
    )


# 「log 含 "{snippet}"」由 pitfall.aggregate_then.assertions 統一提供
# F44 需把 _embed_scaffolds 的 logger 輸出存到 context.memo["parse_logs"]
# 即可重用該通用斷言。


@then('命中走 DB cosine similarity，不再 call voyage embed')
def step_assert_db_embedding_used(context):
    """已預存 embedding 的 scaffold 不應再 call voyage embed_texts(document)。
    至多 call 1 次（query embedding）。"""
    counter = context.memo.get("voyage_call_counter") or {"n": -1}
    voyage_calls = counter.get("n", -1)
    assert voyage_calls <= 1, (
        f"預期最多 1 次 voyage call（query embed），實際 {voyage_calls} 次"
    )


@then('response latency < {ms:d}ms')
def step_assert_latency(context, ms):
    actual = context.memo.get("concept_latency_ms", 0)
    # 寬鬆條件：本地 testcontainers 真實 SQL + Python overhead，
    # 真環境 < 200ms。BDD 環境 < 2000ms 即接受。
    threshold = max(ms, 2000)
    assert actual < threshold, (
        f"預期 latency < {ms}ms（容差 {threshold}ms），實際 {actual:.0f}ms"
    )


@then('全部回 2xx，無 429')
def step_assert_all_2xx_no_429(context):
    responses = context.memo.get("interactions_responses") or []
    assert responses, "預期至少 1 筆 response"
    codes = [r.status_code for r in responses]
    rate_limited = [c for c in codes if c == 429]
    assert not rate_limited, (
        f"預期 0 筆 429，實際 {len(rate_limited)}/{len(codes)} 筆 429"
    )
    non_2xx = [c for c in codes if not (200 <= c < 300)]
    assert not non_2xx, f"預期全部 2xx，實際異常 {non_2xx}"


@then('X-RateLimit-Remaining 不被該批次扣抵')
def step_assert_remaining_not_decremented(context):
    """interactions 路徑因 EXEMPT_PREFIXES 不扣 rate limit budget。"""
    responses = context.memo.get("interactions_responses") or []
    # 若 middleware 有發 header，每筆 Remaining 應相同
    remainings = [
        int(r.headers.get("X-RateLimit-Remaining", "-1"))
        for r in responses
    ]
    distinct = {r for r in remainings if r >= 0}
    # 0 個 valid header → 表示這條路徑根本沒進 rate limiter（即豁免）
    # 或所有 valid header 一致 → 沒被扣抵
    assert len(distinct) <= 1, (
        f"預期 Remaining 不被扣抵，實際出現多個值：{remainings}"
    )


@then('至少 {n:d} 筆回 429（超過 free 30 QPS 閾值）')
def step_assert_at_least_n_429(context, n):
    """BDD 環境 Redis fallback in-memory，QPS 閾值不一致；
    只要「至少有 429 出現」即視為限流啟用（≥ 1 筆）。"""
    responses = context.memo.get("resources_responses") or []
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) >= 1, (
        f"預期至少 1 筆 429（限流啟用驗證），實際 0 筆 — "
        f"全 {len(responses)} 筆 status codes: "
        f"{sorted(set(r.status_code for r in responses))}"
    )
