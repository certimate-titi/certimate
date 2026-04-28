"""Then 步驟 — 驗證 Bloom 分佈/趨勢/結果分析。"""

from behave import then


@then('回應中應包含以下分佈：')
def step_then_distribution(context):
    actual = context.memo.get("bloom_distribution_response")
    assert actual is not None, "尚未呼叫 Bloom 分類統計查詢"

    actual_map = {item["bloom_category"]: item for item in actual}
    for row in context.table:
        cat = row["bloom_category"]
        exp_count = int(row["count"])
        exp_pct = float(row["percentage"])
        item = actual_map.get(cat)
        assert item is not None, f"分佈中缺少 {cat}"
        assert item["count"] == exp_count, (
            f"{cat} count 應為 {exp_count}，實得 {item['count']}"
        )
        assert abs(item["percentage"] - exp_pct) < 0.5, (
            f"{cat} percentage 應為 {exp_pct}，實得 {item['percentage']}"
        )


@then('回應中應包含 {year_a:d} 年與 {year_b:d} 年各自的 Bloom 分佈')
def step_then_trend_years(context, year_a, year_b):
    trend = context.memo.get("bloom_trend_response")
    assert trend is not None, "尚未呼叫年度 Bloom 趨勢查詢"
    assert year_a in trend, f"趨勢資料缺少 {year_a} 年"
    assert year_b in trend, f"趨勢資料缺少 {year_b} 年"


@then('趨勢資料格式應為：')
def step_then_trend_format(context):
    trend = context.memo.get("bloom_trend_response")
    assert trend is not None
    headers = context.table.headings
    bloom_cats = [h for h in headers if h != "year"]
    for row in context.table:
        year = int(row["year"])
        assert year in trend, f"缺少 {year} 年資料"
        actual_year = trend[year]
        for cat in bloom_cats:
            exp = int(row[cat])
            got = actual_year.get(cat, 0)
            assert got == exp, (
                f"{year} 年 {cat} 應為 {exp}，實得 {got}"
            )
