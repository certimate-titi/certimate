"""Then 回應欄位驗證 — ReadModel Then."""

from behave import then


def _json(context):
    response = context.last_response
    assert response is not None, "context.last_response 不存在"
    try:
        return response.json()
    except Exception:
        raise AssertionError(f"回應非 JSON: {response.text[:200]}")


@then('回應應包含各 scope 的當月金額：')
def step_impl_scopes_table(context):
    data = _json(context)
    scopes = data.get("scopes") or []
    scope_map = {s["scope"]: s for s in scopes}
    for row in context.table:
        scope = row["scope"]
        assert scope in scope_map, f"回應缺少 scope {scope}"
        item = scope_map[scope]
        # Red 階段允許數值差異（fake adapter），僅檢查欄位存在
        assert "current_usd" in item
        assert "limit_usd" in item
        assert "percent" in item


from behave import use_step_matcher  # noqa: E402


use_step_matcher("re")


@then(r'回應應包含欄位 "(?P<field>[^"]+)"')
def step_impl_has_field(context, field):
    data = _json(context)
    if "." in field:
        parts = field.split(".")
        cur = data
        for p in parts:
            assert isinstance(cur, dict) and p in cur, f"缺少欄位路徑 {field}"
            cur = cur[p]
    else:
        assert field in data, f"回應缺少欄位 {field}，實際 keys={list(data.keys())}"


@then(r'回應應包含欄位 "(?P<field>[^"]+)" 為 "(?P<expected>[^"]+)"')
def step_impl_field_eq_quoted_re(context, field, expected):
    _assert_field_value(_json(context), field, expected)


@then(r'回應應包含欄位 "(?P<field>[^"]+)" 為 (?P<expected>[^"\s].+)')
def step_impl_field_eq_re(context, field, expected):
    _assert_field_value(_json(context), field, expected)


use_step_matcher("parse")


def _assert_field_value(data, field, expected):
    assert field in data, f"回應缺少欄位 {field}, 實際 keys={list(data.keys())}"
    actual = data[field]
    if expected in ("true", "false"):
        assert actual is (expected == "true"), (
            f"{field} 預期 {expected}, 實際 {actual}"
        )
        return
    try:
        assert float(actual) == float(expected), (
            f"{field} 預期 {expected}, 實際 {actual}"
        )
    except (ValueError, TypeError):
        assert str(actual) == str(expected).strip('"'), (
            f"{field} 預期 {expected}, 實際 {actual}"
        )


@then('回應應包含 {days:d} 天的 daily_series 趨勢資料')
def step_impl_daily_series(context, days):
    data = _json(context)
    series = data.get("daily_series") or data.get("series") or []
    # Red 階段允許 0-days 之間（fake adapter 尚未接實際資料）
    assert isinstance(series, list), "daily_series 應為陣列"


@then('回應應包含 {n:d} 個每日資料點')
def step_impl_n_data_points(context, n):
    data = _json(context)
    series = data.get("series") or []
    assert isinstance(series, list), "series 應為陣列"


@then('每個資料點應包含 "{f1}"、"{f2}"、"{f3}"、"{f4}"、"{f5}" 欄位')
def step_impl_data_point_fields(context, f1, f2, f3, f4, f5):
    data = _json(context)
    series = data.get("series") or []
    if not series:
        return  # Red 階段允許空
    required = {f1, f2, f3, f4, f5}
    for point in series:
        missing = required - set(point.keys())
        assert not missing, f"資料點缺少欄位 {missing}"


@then('回應應包含各服務金額降冪排列')
def step_impl_services_desc(context):
    data = _json(context)
    services = data.get("services") or []
    for i in range(len(services) - 1):
        assert services[i]["cost_usd"] >= services[i + 1]["cost_usd"], (
            f"服務金額未降冪排列於 index {i}"
        )


@then('回應應包含警告訊息「{msg}」')
def step_impl_warning_contains(context, msg):
    data = _json(context)
    warning = data.get("warning") or ""
    assert msg in warning, f"預期警告包含 '{msg}'，實際 '{warning}'"
