# GCP Native Budget 單向同步設計

**文件編號**: AI-cost-monitor-gcp-budget-sync
**產出角色**: 後端工程師 + 安全工程師（CTO 技術線）
**產出日期**: 2026-04-14
**狀態**: Draft v1
**對應 Feature**: 33 — 成本監控中心
**對應 Migration**: 050

---

## 1. 設計目標

讓 Super Admin 在成本監控網頁設定 `AI_GEMINI` 或 `GCP_TOTAL` 預算時，自動在 GCP Billing 後台建立對應的 Native Budget，作為**第二層告警護欄**（app 告警 + GCP Native 告警同時生效）。

### 為什麼只同步這兩個 scope？

| Scope | 可同步？ | 理由 |
|-------|:-------:|------|
| AI_ANTHROPIC | ❌ | Anthropic 是第三方服務，不在 GCP 帳單內 |
| AI_GEMINI | ✅ | Gemini API 走 GCP 計費，可用 service filter 切片 |
| AI_VOYAGE | ❌ | Voyage 是第三方服務，不在 GCP 帳單內 |
| GCP_TOTAL | ✅ | 整個 certimate-titi project 的 GCP 支出 |

## 2. 架構設計

### 2.1 同步方向：單向（App → GCP）

```
┌─────────────────────────┐
│ Super Admin 網頁        │
│ (budget settings panel) │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ cost_monitor_router     │
│   PUT /admin/cost/budget│
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ budget_service.update_budget()  │
│   1. 寫 budget_config           │
│   2. 寫 admin_audit_log         │
│   3. 若 gcp_sync_enabled:       │
│      call gcp_budget_sync_svc   │────┐
└─────────────────────────────────┘    │
                                       ▼
                          ┌──────────────────────┐
                          │ gcp_budget_sync      │
                          │ _service.py          │
                          │   billingbudgets API │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ GCP Billing Budgets  │
                          │ (native)             │
                          └──────────────────────┘
```

**為什麼單向**：
- 雙向同步需要 webhook + conflict resolution，複雜度高
- Super Admin 應以 app 為主要操作介面（單一真實來源）
- GCP 偶發的直接修改由 drift detection 處理

### 2.2 Graceful Degrade

若 GCP API 暫時無法回應或憑證問題：
1. 本地 `budget_config` 仍正常寫入
2. 稽核 log `details.gcp_sync = "failed"` 記錄失敗
3. API 回應帶警告訊息但 status 200
4. 心跳機制週期性 retry（避免 drift 擴大）

## 3. GCP Budget API 呼叫細節

### 3.1 Service Account 權限補充
既有 `cost-monitor-bq-reader` 帳號需加角色：
- `roles/billing.budgetsAdmin`（對 billing account 授權）

```bash
gcloud billing accounts add-iam-policy-binding 0126A9-3FE882-C325F3 \
  --member="serviceAccount:cost-monitor-bq-reader@certimate-titi.iam.gserviceaccount.com" \
  --role="roles/billing.budgetsAdmin"
```

或更保守：建立獨立的 `budget-writer` 服務帳號專門處理同步。

### 3.2 Budget filter 對應表

| App Scope | GCP Budget Filter |
|-----------|-------------------|
| GCP_TOTAL | `projects: ["projects/certimate-titi"]`（全專案）|
| AI_GEMINI | `projects: ["projects/certimate-titi"]` + `services: ["services/<gemini_service_id>"]` |

Gemini API 的 GCP service ID 需在 Layer 3 實作時從 `gcloud billing services list` 查得（對應 `generativelanguage.googleapis.com`）。

### 3.3 Threshold 對應
App 的三級門檻 `warning_percent / degrade_percent / disable_percent` 直接對應 GCP Budget 的 `thresholdRules`。

### 3.4 Display Name 規範
GCP Budget 的 displayName 使用固定前綴方便識別：
```
"[CertiMate:33] AI_GEMINI Budget"
"[CertiMate:33] GCP_TOTAL Budget"
```

## 4. 抽象介面（Layer 3 必須實作）

```python
# backend/app/services/gcp_budget_sync_service.py

from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class SyncResult:
    status: str                # "created" / "updated" / "skipped_non_gcp" / "failed"
    gcp_budget_resource_name: str | None
    error: str | None = None


class GcpBudgetSyncService:
    """GCP Native Budget 單向同步服務。

    Layer 3 實作時需：
    1. 讀取 GCP_BQ_CREDENTIALS_PATH 憑證
    2. 使用 google-cloud-billing-budgets SDK
    3. 實作 upsert_budget / delete_budget / get_budget
    """

    SCOPE_TO_FILTER = {
        "GCP_TOTAL":  {"projects": ["projects/certimate-titi"]},
        "AI_GEMINI":  {
            "projects": ["projects/certimate-titi"],
            "services": ["services/<gemini_service_id>"],  # 待 Layer 3 填入
        },
    }

    def upsert_budget(
        self,
        scope: str,
        monthly_limit_usd: Decimal,
        warning_pct: int,
        degrade_pct: int,
        disable_pct: int,
        existing_resource_name: str | None,
    ) -> SyncResult:
        """若 scope 不可同步（Anthropic / Voyage），回傳 skipped_non_gcp。
        若 existing_resource_name 為 None → 建立新 Budget。
        否則 → 更新既有 Budget。
        失敗不 raise，回傳 SyncResult(status="failed", error=...)。
        """
        raise NotImplementedError("Layer 3 backend engineer must implement")

    def delete_budget(self, resource_name: str) -> None:
        """移除對應的 GCP Native Budget（例如 scope 被刪除時）。"""
        raise NotImplementedError
```

## 5. 整合點：budget_service.update_budget() 偽碼

```python
def update_budget(
    self, super_admin: User, scope: str, new_limit: Decimal, reason: str
) -> dict:
    # 1. 寫本地
    config = self.repo.get_by_scope(scope)
    before = dict(scope=scope, monthly_limit_usd=float(config.monthly_limit_usd))
    config.monthly_limit_usd = new_limit
    config.updated_by = super_admin.id

    # 2. 寫稽核（初步，gcp_sync 尚未決定）
    audit_details = {
        "scope": scope,
        "before": before["monthly_limit_usd"],
        "after": float(new_limit),
        "reason": reason,
        "gcp_sync": "pending",
    }

    # 3. GCP 同步（若啟用）
    warning_message = None
    if config.gcp_sync_enabled:
        result = self.gcp_sync.upsert_budget(
            scope=scope,
            monthly_limit_usd=new_limit,
            warning_pct=config.warning_percent,
            degrade_pct=config.degrade_percent,
            disable_pct=config.disable_percent,
            existing_resource_name=config.gcp_budget_resource_name,
        )
        audit_details["gcp_sync"] = result.status
        if result.status in ("created", "updated"):
            config.gcp_budget_resource_name = result.gcp_budget_resource_name
            config.gcp_last_synced_at = datetime.now(timezone.utc)
        elif result.status == "failed":
            warning_message = "GCP Native Budget 同步失敗，本地預算已更新"
            logger.warning("GCP budget sync failed: %s", result.error)
    else:
        audit_details["gcp_sync"] = "skipped_non_gcp"

    # 4. 寫稽核完整版
    self.audit_repo.create(
        admin_id=super_admin.id,
        action=AuditAction.BUDGET_UPDATED,
        target_type="budget_config",
        target_id=config.id,
        details=audit_details,
    )

    self.db.commit()
    return {
        "ok": True,
        "warning": warning_message,
        "gcp_sync_status": audit_details["gcp_sync"],
    }
```

## 6. Drift Detection（心跳）

每日心跳檢查 `gcp_sync_enabled = true` 的 scope：
1. 從 GCP 讀取對應 Budget 的金額
2. 與本地 `monthly_limit_usd` 比對
3. 若不一致：
   - 寫入告警日誌
   - 通知 Super Admin（email + 站內）
   - **不自動修正**（避免覆蓋 GCP Console 上的手動調整）

## 7. 測試策略

### Unit tests
- `gcp_budget_sync_service` 的各回傳狀態（created/updated/skipped/failed）走 mock SDK
- SCOPE_TO_FILTER 對應正確

### BDD E2E
Mock `billingbudgets` SDK 為 fake adapter，驗證：
- AI_GEMINI 首次設定建立 budget
- GCP_TOTAL 更新既有 budget
- AI_ANTHROPIC 不呼叫 API
- API 失敗時本地更新仍成功

## 8. 給 CTO 的三句話

1. **單向推送**是最佳 cost/benefit：簡單但有效，避免雙向同步的 conflict 惡夢
2. **Graceful degrade** 絕對不能省：GCP API 偶爾抽風不能影響 app 主流程
3. Layer 3 實作時 Gemini service ID 需先用 `gcloud billing services list | grep -i gemini` 查出來填入 SCOPE_TO_FILTER
