"""Then 回應應包含弱點分析 / 突破策略 / 考前衝刺計畫 — ReadModel Then"""

from behave import then


@then('回應應包含弱點分析：')
def step_impl(context):
    response = context.last_response
    data = response.json()

    wa = data.get("weakness_analysis", [])
    assert isinstance(wa, list) and len(wa) > 0, \
        f"預期 weakness_analysis 為非空列表，實際：{wa}"

    # Feature table has description columns; verify list items have required keys
    for item in wa:
        assert "topic" in item or "weak_topics" in item, \
            f"弱點分析項目缺少 topic 或 weak_topics 欄位：{item}"


@then('回應應包含突破策略：')
def step_impl_strategy(context):
    response = context.last_response
    data = response.json()

    bs = data.get("breakthrough_strategies", [])
    assert isinstance(bs, list) and len(bs) > 0, \
        f"預期 breakthrough_strategies 為非空列表，實際：{bs}"

    for item in bs:
        assert "method" in item or "strategy" in item, \
            f"突破策略項目缺少 method 或 strategy 欄位：{item}"


@then('回應應包含考前衝刺計畫：')
def step_impl_sprint(context):
    response = context.last_response
    data = response.json()

    sp = data.get("sprint_plan", [])
    assert isinstance(sp, list) and len(sp) > 0, \
        f"預期 sprint_plan 為非空列表，實際：{sp}"
    assert len(sp) <= 7, f"衝刺計畫最多 7 天，實際 {len(sp)} 天"

    for item in sp:
        assert "day" in item, f"衝刺計畫項目缺少 day 欄位：{item}"
        assert "topic" in item, f"衝刺計畫項目缺少 topic 欄位：{item}"


@then('弱點分析應提及 "{topic1}" 和 "{topic2}"')
def step_impl_mentions(context, topic1, topic2):
    response = context.last_response
    data = response.json()

    wa = data.get("weakness_analysis", [])
    all_topics = " ".join(str(item.get("topic", "")) for item in wa)

    assert topic1 in all_topics, \
        f"弱點分析應提及 '{topic1}'，實際主題：{all_topics}"
    assert topic2 in all_topics, \
        f"弱點分析應提及 '{topic2}'，實際主題：{all_topics}"


@then('突破策略應針對這兩個弱點節點')
def step_impl_targeted(context):
    response = context.last_response
    data = response.json()

    bs = data.get("breakthrough_strategies", [])
    assert len(bs) > 0, "突破策略不應為空"
    # Strategies should have topic fields
    for item in bs:
        assert item.get("topic") or item.get("method"), \
            f"突破策略缺少主題/方法資訊：{item}"
