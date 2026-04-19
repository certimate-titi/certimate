# GCP Billing Export 功能 — 實現總結

**狀態**: ✅ **實現完成**  
**最後更新**: 2026-04-17

## 概述

Feature 33 的 **GCP Billing Export** 功能已實現完整，包括：
- ✅ `GcpBillingService` — BigQuery SQL 查詢層
- ✅ 環境變數配置（`config.py`）
- ✅ 錯誤處理與日誌
- ✅ BDD 測試集成（test hooks）
- ✅ 配置指南文檔

## 實現要點

### 1. SQL 查詢修正

**問題**: 原始 SQL 使用 `_PARTITIONTIME`，但 GCP Billing Export 表實際分區欄位是 `export_time`

**修正**:
```python
# ❌ 舊
WHERE DATE(_PARTITIONTIME) >= DATE('...')

# ✅ 新
WHERE DATE(export_time) >= DATE('...')
```

**影響的方法**:
- `_load_monthly_summary_real()` — 查詢當月服務分類成本
- `_load_daily_trend_real()` — 查詢 30 天每日趨勢

### 2. 環境變數配置

在 `backend/app/core/config.py` 中新增：

```python
# GCP Billing Export 設定（Feature 33）
self.GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
self.GCP_BILLING_EXPORT_DATASET: str = os.environ.get(
    "GCP_BILLING_EXPORT_DATASET", "billing_export"
)
self.GCP_BILLING_EXPORT_TABLE: str = os.environ.get(
    "GCP_BILLING_EXPORT_TABLE", "gcp_billing_export_v1"
)
self.GCP_BQ_CREDENTIALS_PATH: str = os.environ.get("GCP_BQ_CREDENTIALS_PATH", "")
self.GCP_BILLING_MODE: str = os.environ.get("GCP_BILLING_MODE", "fake")

# GCP Native Budget API 設定
self.GCP_BUDGET_PARENT: str = os.environ.get("GCP_BUDGET_PARENT", "")

# 成本監控預警通知設定
self.COST_ALERT_EMAILS: str = os.environ.get("COST_ALERT_EMAILS", "")
```

### 3. 改進的錯誤處理

新增詳細的錯誤訊息，幫助部署人員快速診斷問題：

```python
GcpBillingUnavailable("GCP_PROJECT_ID 未設定")
GcpBillingUnavailable("GCP_BQ_CREDENTIALS_PATH 檔案不存在: /path/to/key.json")
GcpBillingUnavailable(f"無法初始化 GCP BigQuery client: {exc}")
```

### 4. BDD 測試集成

**新增測試鉤子** — 在 `GcpBillingService` 中：

```python
def set_test_services(services: list[dict] | None) -> None:
    """Inject services list from feature table."""

def set_test_daily_series(daily_series: list[dict] | None) -> None:
    """Inject daily trend data from feature table."""
```

**步驟定義更新** — 在 `aggregate_given/misc_given.py`：

```gherkin
Given BigQuery Billing Export 有以下資料：
  | service              | cost_usd | billing_date |
  | Cloud Run            | 120.00   | 2026-04-01   |
  | Cloud SQL            | 180.25   | 2026-04-01   |
  ...
```

**環境清理** — 在 `environment.py` 的 `after_scenario()` 中：

```python
from app.services.gcp_billing_service import set_test_override, set_test_services
set_test_override(None)
set_test_services(None)
set_test_daily_series(None)
```

## 部署檢查清單

### 開發環境（本地）

```bash
# 1. 啟用 fake 模式（默認）
GCP_BILLING_MODE=fake

# 2. 執行 BDD 測試（需要 Docker）
cd backend
docker ps  # 確認 Docker 可用
.venv/bin/python -m behave tests/features/33-成本監控中心.feature --tags=~@ignore

# 3. 測試 API（回傳 stub 資料）
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/admin/cost/gcp/services
```

**預期回應**（Fake 模式）:
```json
{
  "total_usd": 450.95,
  "services": [
    {"service_name": "Cloud SQL", "cost_usd": 180.25},
    {"service_name": "Cloud Run", "cost_usd": 120.00},
    ...
  ],
  "cached_at": "2026-04-17T12:34:56.789Z",
  "period_start": "2026-04-01",
  "period_end": "2026-04-17"
}
```

### 生產環境（Cloud Run）

```bash
# 1. 設定環境變數
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --set-env-vars GCP_PROJECT_ID=certimate-titi \
  --set-env-vars GCP_BILLING_EXPORT_DATASET=billing_export \
  --set-env-vars GCP_BILLING_EXPORT_TABLE=gcp_billing_export_v1 \
  --set-env-vars GCP_BQ_CREDENTIALS_PATH=/var/secrets/gcp-billing/key.json

# 2. 掛載 Service Account key（需在 Cloud Run 配置中）
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --service-account=certimate-billing@certimate-titi.iam.gserviceaccount.com

# 3. 驗證配置
gcloud run services describe certimate-api --format="value(spec.template.spec.containers[0].env)"

# 4. 查看日誌（排查問題）
gcloud run services logs read certimate-api --limit 100
```

## API 端點確認

| 端點 | 方法 | 權限 | 功能 |
|------|------|------|------|
| `/admin/cost/summary` | GET | super_admin | 當月成本總覽（四個 scope） |
| `/admin/cost/providers/{provider}` | GET | super_admin | 單一供應商詳情（token 級） |
| `/admin/cost/gcp/services` | GET | super_admin | **GCP 服務分類成本** ← billing_export |
| `/admin/cost/trends?days=30` | GET | super_admin | 成本趨勢圖（30 天） |

## 故障排除

### 開發環境

**問題**: 測試時收到 `GCP_BILLING_NOT_CONFIGURED`

**原因**: `GCP_BILLING_MODE=real` 但未配置 credentials

**解決**:
```bash
# 檢查設定
echo $GCP_BILLING_MODE  # 應為 "fake" 或未設定

# 若想測試真實模式
export GCP_BILLING_MODE=fake  # 回到 fake（默認）
```

### 生產環境

**問題**: API 回傳 503 `GCP_BILLING_TEMPORARILY_UNAVAILABLE`

**可能原因**:
1. Service Account 缺少 `bigquery.dataViewer` 角色
2. `GCP_PROJECT_ID` 錯誤
3. BigQuery Billing Export dataset 未啟用

**診斷**:
```bash
# 1. 檢查 Service Account 角色
gcloud projects get-iam-policy certimate-titi \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"

# 2. 驗證 BigQuery dataset 存在
bq ls --dataset_id=certimate-titi:billing_export

# 3. 測試查詢
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) FROM `certimate-titi.billing_export.gcp_billing_export_v1_*`'

# 4. 查看 Cloud Run 日誌
gcloud run services logs read certimate-api --limit 50 | grep -i "billingquery"
```

## 未來優化

1. **Redis 快取** — 將查詢結果快取 1 小時（已實現 TTL cache，支援 Redis）
2. **GCP Budget 同步** — 與 GCP Native Budget API 同步
3. **成本告警** — 達到門檻時自動發送 email

## 相關文件

- 📄 [GCP Billing Export 設定指南](./GCP_BILLING_EXPORT_SETUP.md)
- 📋 [Feature 33 — 成本監控中心.feature](../backend/tests/features/33-成本監控中心.feature)
- 🔧 [GcpBillingService 實現](../backend/app/services/gcp_billing_service.py)
- ⚙️ [CostMonitorService 整合](../backend/app/services/cost_monitor_service.py)

## 驗收標準

- [x] SQL 查詢使用正確的欄位名（`export_time`）
- [x] 環境變數在 `config.py` 中定義
- [x] 錯誤處理適當（捕捉 `GcpBillingUnavailable`）
- [x] 日誌詳細（包含初始化、查詢、清除緩存）
- [x] BDD 步驟實現（feature table 注入、清理鉤子）
- [x] 配置文檔完整（本地/Cloud Run 部署)
- [x] API 端點已測試（回傳 stub 資料）

## 待執行項目

### 立即執行

```bash
# 設定 Cloud Run 環境變數
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --set-env-vars GCP_PROJECT_ID=certimate-titi \
  --set-env-vars GCP_BILLING_EXPORT_DATASET=billing_export

# 掛載 Service Account key（通過 Workload Identity）
gcloud run services update certimate-api \
  --service-account=certimate-billing@certimate-titi.iam.gserviceaccount.com
```

### BDD 測試驗收

```bash
# 需要 Docker + PostgreSQL
cd backend && docker run -d -e POSTGRES_PASSWORD=postgres postgres:15
.venv/bin/python -m behave tests/features/33-成本監控中心.feature --tags=~@ignore
```

### 監控與告警（可選）

```bash
# 設定成本預警 email
export COST_ALERT_EMAILS=ops@certimate.com,cto@certimate.com

# 設定 GCP Budget parent（用於同步）
export GCP_BUDGET_PARENT=billingAccounts/012345-ABCDEF-GHIJKL
```
