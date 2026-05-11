"""Then assertions — Feature 37 BDD."""

from behave import then


@then('回應 {code:d}')
def step_assert_status(context, code):
    resp = context.last_response
    assert resp.status_code == code, (
        f"預期 {code}，實際 {resp.status_code} body={resp.text[:200]}"
    )


@then('回應 200 且 scaffolds 中至少 1 筆 type=takeaway')
def step_assert_parsed_has_takeaway(context):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text[:200]}"
    data = resp.json()
    scaffolds = data.get("scaffolds") or []
    takeaway = [s for s in scaffolds if s.get("type") == "takeaway"]
    assert takeaway, f"預期至少 1 筆 type=takeaway scaffold，實際 0 筆"
    context.memo["last_parsed_takeaway"] = takeaway[0]


@then('該 scaffold 的 retrieval_prompt 為 "{value}"')
def step_assert_takeaway_retrieval_prompt(context, value):
    sf = context.memo.get("last_parsed_takeaway")
    assert sf is not None, "需先執行『回應 200 且 scaffolds 中至少 1 筆 type=takeaway』"
    actual = sf.get("retrieval_prompt")
    assert actual == value, f"預期 retrieval_prompt={value!r}，實際={actual!r}"


@then('該 scaffold 的 template_code 為 "{code}"')
def step_assert_takeaway_template_code(context, code):
    sf = context.memo.get("last_parsed_takeaway")
    assert sf is not None, "需先執行『回應 200 且 scaffolds...』"
    actual = sf.get("template_code")
    assert actual == code, f"預期 template_code={code!r}，實際={actual!r}"


@then('scaffolds 中所有 type=strategy 的項目 retrieval_prompt 為 null')
def step_assert_strategy_retrieval_null(context):
    resp = context.last_response
    data = resp.json()
    strategy_rows = [s for s in (data.get("scaffolds") or []) if s.get("type") == "strategy"]
    assert strategy_rows, "預期至少 1 筆 type=strategy scaffold"
    for s in strategy_rows:
        assert s.get("retrieval_prompt") is None, (
            f"strategy retrieval_prompt 應為 null，實際={s.get('retrieval_prompt')!r}"
        )


@then('回應 200 含 log_id')
def step_assert_interaction_logged(context):
    resp = context.last_response
    assert resp.status_code == 200, f"預期 200，實際 {resp.status_code} body={resp.text[:200]}"
    data = resp.json()
    assert data.get("log_id"), f"預期 log_id，實際 keys={list(data.keys())}"


@then('scaffold_interaction_log 表新增一筆 (scaffold_id={label}, event={event})')
def step_assert_log_row_scaffold_event(context, label, event):
    from app.models.scaffold_interaction_log import ScaffoldInteractionLog
    db = context.db_session
    aliases = context.memo.get("scaffold_aliases", {})
    if label not in aliases:
        raise AssertionError(f"scaffold alias {label!r} 未建立")
    sf_id = aliases[label]
    rows = db.query(ScaffoldInteractionLog).filter_by(
        scaffold_id=sf_id, event=event,
    ).all()
    assert rows, f"預期 log (scaffold={label}, event={event}) 至少 1 筆，實際 0 筆"


@then('scaffold_interaction_log 表新增一筆 (event={event}, recall_quality={quality})')
def step_assert_log_row_event_quality(context, event, quality):
    from app.models.scaffold_interaction_log import ScaffoldInteractionLog
    db = context.db_session
    rows = db.query(ScaffoldInteractionLog).filter_by(
        event=event, recall_quality=quality,
    ).all()
    assert rows, (
        f"預期 log (event={event}, recall_quality={quality}) 至少 1 筆，實際 0 筆"
    )


@then('回應 422 含訊息 "{snippet}"')
def step_assert_422_with_message(context, snippet):
    resp = context.last_response
    assert resp.status_code == 422, f"預期 422，實際 {resp.status_code}"
    body = resp.text
    assert snippet in body, f"預期 422 body 含 {snippet!r}，實際:\n{body[:200]}"


@then('page_range 為 [{a:d}, {b:d}]')
def step_assert_page_range_pair(context, a, b):
    resp = context.last_response
    data = resp.json()
    assert data.get("page_range") == [a, b], (
        f"預期 page_range=[{a},{b}]，實際={data.get('page_range')!r}"
    )


@then('page_range 為 []')
def step_assert_page_range_empty(context):
    resp = context.last_response
    data = resp.json()
    assert data.get("page_range") == [], (
        f"預期 page_range=[]，實際={data.get('page_range')!r}"
    )


@then('questions 陣列長度為 {n:d}')
def step_assert_questions_length(context, n):
    resp = context.last_response
    data = resp.json()
    questions = data.get("questions") or []
    assert len(questions) == n, (
        f"預期 questions 長度 {n}，實際 {len(questions)}"
    )


@then('每題物件含 content / option_a / option_b / option_c / option_d / correct_answer')
def step_assert_question_shape(context):
    resp = context.last_response
    data = resp.json()
    required = {"content", "option_a", "option_b", "option_c", "option_d", "correct_answer"}
    for q in data.get("questions") or []:
        missing = required - set(q.keys())
        assert not missing, f"題目缺欄位 {missing}，實際 keys={list(q.keys())}"
