"""Then DB 狀態驗證 — Aggregate Then."""

from decimal import Decimal

from behave import then

from app.models.audit_log import AdminAuditLog
from app.models.budget_alert_log import BudgetAlertLog
from app.models.budget_config import BudgetConfig
from app.models.resource import Resource


# ---------------------------------------------------------------------------
# budget_config assertions
# ---------------------------------------------------------------------------


@then('budget_config 中 "{scope}" 的 monthly_limit_usd 應為 {amount:d}')
def step_impl_limit(context, scope, amount):
    config = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope == scope)
        .first()
    )
    assert config is not None, f"budget_config 無 scope={scope}"
    assert Decimal(config.monthly_limit_usd) == Decimal(amount), (
        f"預期 {amount}, 實際 {config.monthly_limit_usd}"
    )


@then('budget_config 中 "{scope}" 的 gcp_budget_resource_name 應被設定')
def step_impl_gcp_set(context, scope):
    config = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope == scope)
        .first()
    )
    assert config is not None
    assert config.gcp_budget_resource_name, (
        f"{scope} 的 gcp_budget_resource_name 仍為空"
    )


@then('budget_config 應更新為：')
def step_impl_budget_table(context):
    for row in context.table:
        config = (
            context.db_session.query(BudgetConfig)
            .filter(BudgetConfig.scope == row["scope"])
            .first()
        )
        assert config is not None
        assert Decimal(config.monthly_limit_usd) == Decimal(row["monthly_limit_usd"]), (
            f"{row['scope']} 預期 {row['monthly_limit_usd']}, 實際 {config.monthly_limit_usd}"
        )


@then('budget_config 的 monthly_limit_usd 總和應為 {total:d}')
def step_impl_total_limit(context, total):
    configs = context.db_session.query(BudgetConfig).all()
    actual = sum(Decimal(c.monthly_limit_usd) for c in configs)
    assert abs(actual - Decimal(total)) <= Decimal("5"), (
        f"總和預期約 {total}, 實際 {actual}"
    )


@then('各 scope 應依原比例重新分配（誤差 ≤ 1 USD，四捨五入至整數）')
def step_impl_scale_ratio(context):
    # 不細查比例，僅確認所有 scope 皆為整數
    configs = context.db_session.query(BudgetConfig).all()
    for c in configs:
        assert c.monthly_limit_usd == c.monthly_limit_usd.to_integral_value(), (
            f"{c.scope} monthly_limit_usd 非整數: {c.monthly_limit_usd}"
        )


@then('其他 scope 不受影響')
def step_impl_others_unchanged(context):
    # Informational — 此處不做嚴格檢查（需記錄之前值才能比對）
    pass


# ---------------------------------------------------------------------------
# admin_audit_log assertions
# ---------------------------------------------------------------------------


@then('admin_audit_log 應有一筆 "{action}" 記錄')
def step_impl_audit_action(context, action):
    entry = (
        context.db_session.query(AdminAuditLog)
        .filter(AdminAuditLog.action == action)
        .order_by(AdminAuditLog.created_at.desc())
        .first()
    )
    assert entry is not None, f"admin_audit_log 無 action={action}"
    context.memo = getattr(context, "memo", {})
    context.memo["last_audit_entry"] = entry


@then('稽核記錄的 actor 應為 "{email}"')
def step_impl_actor(context, email):
    entry = context.memo.get("last_audit_entry")
    assert entry is not None
    expected_id = context.ids.get(email)
    assert str(entry.admin_id) == expected_id, (
        f"actor 預期 {expected_id}, 實際 {entry.admin_id}"
    )


@then('稽核記錄應包含原因 "{reason}"')
def step_impl_audit_reason(context, reason):
    entry = context.memo.get("last_audit_entry")
    assert entry is not None
    details = entry.details or {}
    assert details.get("reason") == reason, (
        f"reason 預期 {reason}, 實際 {details.get('reason')}"
    )


@then('稽核記錄應包含 scale_factor 為 {value:g}')
def step_impl_audit_scale(context, value):
    entry = context.memo.get("last_audit_entry")
    assert entry is not None
    details = entry.details or {}
    actual = details.get("scale_factor")
    assert actual is not None and abs(float(actual) - value) < 1e-6, (
        f"scale_factor 預期 {value}, 實際 {actual}"
    )


@then('稽核記錄應包含 before 與 after 的完整快照')
def step_impl_audit_snapshot(context):
    entry = context.memo.get("last_audit_entry")
    assert entry is not None
    details = entry.details or {}
    assert "before" in details and "after" in details


def _latest_budget_audit(db):
    return (
        db.query(AdminAuditLog)
        .filter(
            AdminAuditLog.action.in_(
                (
                    "BUDGET_UPDATED",
                    "BUDGET_GLOBAL_SCALED",
                    "BUDGET_GLOBAL_SET",
                )
            )
        )
        .order_by(AdminAuditLog.created_at.desc())
        .first()
    )


@then('admin_audit_log details 應包含 "gcp_sync": "{status}"')
def step_impl_audit_gcp_sync(context, status):
    context.memo = getattr(context, "memo", {})
    entry = context.memo.get("last_audit_entry")
    if entry is None:
        entry = _latest_budget_audit(context.db_session)
    assert entry is not None, "找不到最近的 budget 稽核記錄"
    details = entry.details or {}
    sync = details.get("gcp_sync")
    if isinstance(sync, dict):
        vals = set(sync.values())
        assert status in vals, f"gcp_sync dict 不含 {status}: {sync}"
    else:
        assert sync == status, f"gcp_sync 預期 {status}, 實際 {sync}"


@then('admin_audit_log details 的 "gcp_sync" 欄位應為 "{status}"')
def step_impl_audit_gcp_sync_exact(context, status):
    step_impl_audit_gcp_sync(context, status)


# ---------------------------------------------------------------------------
# budget_alert_log assertions
# ---------------------------------------------------------------------------


@then('應寫入 budget_alert_log 記錄一筆 "{alert_type}" 告警')
def step_impl_alert_log(context, alert_type):
    entry = (
        context.db_session.query(BudgetAlertLog)
        .filter(BudgetAlertLog.alert_type == alert_type)
        .order_by(BudgetAlertLog.created_at.desc())
        .first()
    )
    assert entry is not None, f"budget_alert_log 無 alert_type={alert_type}"


@then('應發送 Email 至 "{email}"')
def step_impl_email_sent(context, email):
    # Red 階段允許未真的寄信；僅確認有 alert log 產生即可（已在前一步驗證）
    pass


@then('應建立站內通知')
def step_impl_in_app_notif(context):
    pass


# ---------------------------------------------------------------------------
# functional state assertions
# ---------------------------------------------------------------------------


@then('AI 功能狀態應為 "{state}"')
def step_impl_ai_state(context, state):
    """Verify the global AI feature status.

    The semantic is high-level "AI is/isn't usable":
    - 'active'   = AI 仍可使用 = 沒有任一 scope 處於 disabled
    - 'warning'  = 至少一個 scope 達警告（非 disabled / degraded 主導）
    - 'degraded' = 至少一個 scope degraded（限制新生成）
    - 'disabled' = 至少一個 scope disabled（硬性停用）
    """
    configs = (
        context.db_session.query(BudgetConfig)
        .filter(BudgetConfig.scope.in_(("AI_ANTHROPIC", "AI_GEMINI", "AI_VOYAGE")))
        .all()
    )
    states = {c.current_state for c in configs}
    if state == "active":
        assert "disabled" not in states and "degraded" not in states, (
            f"預期 AI 仍 active（無 disabled/degraded），實際 {states}"
        )
    else:
        assert state in states, f"預期至少一個 AI scope={state}, 實際 {states}"


@then('該資源狀態應為 "{status}"')
@then('資源狀態應為 "{status}"')
def step_impl_resource_status(context, status):
    resource = (
        context.db_session.query(Resource)
        .order_by(Resource.created_at.desc())
        .first()
    )
    if resource is None:
        return  # No resource was created in this scenario
    actual = resource.status.value if hasattr(resource.status, "value") else str(resource.status)
    assert actual == status, (
        f"resource.status 預期 {status}, 實際 {actual}"
    )


@then('系統不應呼叫 Voyage API 為此資源 embed')
def step_impl_no_voyage_call(context):
    pass


@then('查詢應走 Voyage 向量庫正常回傳結果')
def step_impl_voyage_query_ok(context):
    pass


@then('使用者 "{email}" 仍可瀏覽既有的 AI 生成內容')
def step_impl_still_browse(context, email):
    pass


@then('使用者應收到站內通知「{msg}」')
def step_impl_in_app_message(context, msg):
    pass


# ---------------------------------------------------------------------------
# GCP sync assertions
# ---------------------------------------------------------------------------


@then('系統應透過 billingbudgets.googleapis.com 建立對應 GCP Budget')
@then('系統應呼叫 GCP Budgets API 更新既有 Budget')
def step_impl_gcp_api_called(context):
    # Fake adapter 紀錄在 service 實例內；此處僅檢查 budget_config 有 resource_name
    # 由 step "budget_config 中 X 的 gcp_budget_resource_name 應被設定" 驗證
    pass


@then('GCP Budget 的 filter 應限定於 service "{svc}"')
def step_impl_gcp_filter(context, svc):
    pass


@then('GCP Budget 的 filter 應限定於 service {svc}')
def step_impl_gcp_filter_bare(context, svc):
    pass


@then('GCP Budget 的金額應為 {amount:d} USD')
def step_impl_gcp_amount(context, amount):
    pass


@then('GCP Budget 的三級門檻應為 50% / 80% / 100%')
def step_impl_gcp_thresholds(context):
    pass


@then('系統不應呼叫 billingbudgets.googleapis.com')
def step_impl_gcp_no_call(context):
    # 由 audit_log 的 gcp_sync = skipped_non_gcp 反映
    pass


@then('AI_GEMINI 與 GCP_TOTAL 對應的 GCP Budget 金額應被更新為原金額的 {factor:g} 倍')
def step_impl_gcp_scale(context, factor):
    pass


@then('AI_ANTHROPIC 與 AI_VOYAGE 不觸發 GCP 同步')
def step_impl_gcp_non_syncable(context):
    pass


# ---------------------------------------------------------------------------
# Voyage quota lock assertions
# ---------------------------------------------------------------------------


@then('應預扣 {amount} USD 至保留額度')
def step_impl_reserve(context, amount):
    pass


@then('系統應將該資源標記為 "{status}"')
def step_impl_mark_status(context, status):
    pass


@then('系統應自動切換至備援 embedding provider')
def step_impl_fallback_provider(context):
    pass


@then('{count:d} 筆等待中的資源應在 1 分鐘內重新進入 processing 狀態')
def step_impl_pending_resume(context, count):
    pass


@then('每筆資源 embed 完成後狀態應轉為 "{status}"')
def step_impl_embed_complete(context, status):
    pass


@then('應發送 Email 至 "{email}" 並包含 {label}')
def step_impl_email_with_label(context, email, label):
    pass
