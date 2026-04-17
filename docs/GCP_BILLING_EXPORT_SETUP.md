# GCP Billing Export 功能 — 設定指南

本文件說明如何配置 Feature 33（成本監控中心）的 GCP Billing Export 功能。

## 概述

GCP Billing Export 允許 CertiMate 從 Google Cloud BigQuery 中查詢歷史帳單資料，實現：
- **當月服務分類成本** — 按 Cloud Run、Cloud SQL 等服務分類顯示成本
- **每日成本趨勢** — 視覺化最近 30 天的成本走勢
- **無月度 API 調用額度限制** — BigQuery Billing Export 是完整的帳單紀錄，無 rate limit

## 前置條件

1. **GCP 專案** — 已啟用 Billing 並連結至 Cloud Billing Account
2. **BigQuery Billing Export** — 已啟用，表自動建立於 `billing_export` dataset
3. **Service Account** — 具 `bigquery.dataViewer` 權限
4. **已安裝** — `pip install google-cloud-bigquery`（可選，fake 模式下不需要）

## 設定步驟

### 1. 啟用 GCP BigQuery Billing Export

進入 [GCP Billing Console](https://console.cloud.google.com/billing)：

```
1. 選擇 Cloud Billing Account
2. 點選左側 "Billing Export"
3. 在 "BigQuery Export" 標籤中，點 "EDIT SETTINGS"
4. 選擇目標專案（通常選你的應用專案）
5. 設定 Dataset ID：billing_export（或自訂）
6. 點 "SAVE"
```

**結果**：BigQuery 中自動建立：
```
project_id.billing_export.gcp_billing_export_v1_{YYYYMM}
```
例如：`certimate-titi.billing_export.gcp_billing_export_v1_202604`

### 2. 建立 Service Account

進入 [GCP IAM Console](https://console.cloud.google.com/iam-admin/serviceaccounts)：

```
1. 點 "CREATE SERVICE ACCOUNT"
2. Service account name: certimate-billing-export
3. Grant these roles:
   - BigQuery Data Viewer
   - BigQuery Read Session User
4. 建立 JSON key：
   - 點進 Service Account 詳情
   - "Keys" 標籤 → "ADD KEY" → "Create new key" → JSON
   - 下載 JSON 檔案（保管好，勿提交 git！）
```

### 3. 部署環境變數

將以下環境變數添加到 Cloud Run 或本地 `.env`：

```bash
# 必需
GCP_PROJECT_ID=certimate-titi
GCP_BILLING_EXPORT_DATASET=billing_export
GCP_BILLING_EXPORT_TABLE=gcp_billing_export_v1
GCP_BQ_CREDENTIALS_PATH=/path/to/service-account.json
GCP_BILLING_MODE=real

# 可選（用於預算超限告警）
GCP_BUDGET_PARENT=billingAccounts/012345-ABCDEF-GHIJKL
COST_ALERT_EMAILS=ops@certimate.com,cto@certimate.com
```

#### Cloud Run 部署

使用 `gcloud run services update` 設定環境變數：

```bash
# 設定為真實模式（需要 credentials 檔案）
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --set-env-vars GCP_PROJECT_ID=certimate-titi \
  --set-env-vars GCP_BILLING_EXPORT_DATASET=billing_export \
  --set-env-vars GCP_BQ_CREDENTIALS_PATH=/var/secrets/gcp-billing/key.json

# 掛載 service account key 到容器
# （需在 Cloud Run 配置中啟用 workload identity 或掛載 secret）
```

#### 本地開發

建立 `.env` 檔案：

```bash
GCP_PROJECT_ID=certimate-titi
GCP_BILLING_EXPORT_DATASET=billing_export
GCP_BILLING_EXPORT_TABLE=gcp_billing_export_v1
GCP_BQ_CREDENTIALS_PATH=/Users/simon/gcp-keys/certimate-billing-export.json
GCP_BILLING_MODE=real
```

### 4. 驗證配置

在後端執行以下測試：

```bash
cd backend

# Python shell
python3
>>> from app.services.gcp_billing_service import GcpBillingService
>>> service = GcpBillingService()
>>> service._is_configured()
True

# 測試查詢
>>> from datetime import datetime
>>> now = datetime.now()
>>> summary = service.get_monthly_summary(now.year, now.month)
>>> print(f"Total: ${summary.total_usd}")
>>> for s in summary.services[:3]:
...     print(f"  {s.service_name}: ${s.cost_usd}")
```

或透過 API 測試：

```bash
# 本地 API 伺服器
cd backend
.venv/bin/python -m uvicorn app.main:app --reload

# Super Admin 登入後（在前端或用 Postman）
curl -H "Authorization: Bearer <super_admin_token>" \
  http://localhost:8000/api/v1/admin/cost/gcp/services
```

## BigQuery 表結構

GCP Billing Export 表的標準欄位：

```sql
-- 主要欄位
service.description    STRING   -- 服務名稱（"Cloud Run", "Cloud SQL" 等）
cost                   FLOAT64  -- 成本金額
currency               STRING   -- 貨幣代碼（"USD"）
export_time            TIMESTAMP -- 導出時間（分區欄位）
usage_start_time       TIMESTAMP
usage_end_time         TIMESTAMP
project.id             STRING   -- GCP 專案 ID
labels                 RECORD   -- 自訂標籤

-- SQL 範例
SELECT
  service.description,
  ROUND(SUM(cost), 2) as total_cost
FROM `project_id.billing_export.gcp_billing_export_v1_*`
WHERE DATE(export_time) >= DATE('2026-04-01')
  AND DATE(export_time) <= DATE('2026-04-30')
  AND currency = 'USD'
GROUP BY service.description
ORDER BY total_cost DESC
```

## 故障排除

### 「GCP_BILLING_EXPORT_DATASET 未設定」

**原因**：環境變數未正確配置

**解決**：
```bash
# 檢查 .env
cat .env | grep GCP_BILLING

# 或設定環境變數
export GCP_BILLING_EXPORT_DATASET=billing_export
export GCP_BQ_CREDENTIALS_PATH=/path/to/key.json
```

### 「GCP_BQ_CREDENTIALS_PATH 檔案不存在」

**原因**：Service Account JSON 檔案路徑錯誤

**解決**：
1. 確認 JSON 檔案存在且路徑正確
2. 檢查檔案權限：`ls -la /path/to/key.json`
3. 在 Cloud Run 中，可能需要使用 Workload Identity 而非檔案方式

### 「BigQuery 查詢失敗: 403 Forbidden」

**原因**：Service Account 缺少必要權限

**解決**：
```bash
# 在 GCP IAM 中確認角色
gcloud projects get-iam-policy certimate-titi \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"

# 若缺少 bigquery.dataViewer，手動添加
gcloud projects add-iam-policy-binding certimate-titi \
  --member=serviceAccount:certimate-billing@certimate-titi.iam.gserviceaccount.com \
  --role=roles/bigquery.dataViewer
```

### API 回傳 503「GCP billing 暫時無法取得」

**原因**：
1. BigQuery 連線失敗
2. 表名不存在
3. SQL 查詢有誤

**解決**：
1. 檢查日誌：`docker logs <container_id> | grep "BigQuery"`
2. 直接在 BigQuery 中執行 SQL 測試
3. 確認 `GCP_BILLING_MODE=real` 已設定

## 開發模式（Fake）

默認情況下，系統以 **Fake 模式**運行，回傳 stub 數據：

```python
GCP_BILLING_MODE=fake  # 默認
```

此時 API 不依賴真實的 BigQuery，回傳預先定義的測試資料：
- Cloud SQL: $180.25
- Cloud Run: $120.00
- Gemini API: $85.20
- 等等...

## Stub 資料覆蓋（BDD 測試用）

在 BDD 測試中，可動態設定 monthly total：

```python
from app.services.gcp_billing_service import set_test_override
from decimal import Decimal

# 設定當月 GCP 成本為 450.95 USD
set_test_override(Decimal("450.95"))

# 測試完後重置
set_test_override(None)
```

## 成本預估

GCP Billing Export：
- 儲存成本：~$0.10/GB/月（billing_export dataset 通常 <1GB）
- 查詢成本：$6.25/TB（CertiMate 每天查詢一次，~1MB，成本 negligible）
- **總計**：基本上免費

## 下一步

1. 在 Feature 33 的 BDD 測試中驗證：
   ```bash
   .venv/bin/python -m behave tests/features/33-成本監控中心.feature
   ```

2. 設定 GCP Native Budget API（可選）— 與 GCP 內置預算告警同步

3. 配置成本告警 Email（可選） — 設定 `COST_ALERT_EMAILS`

## 參考資源

- [GCP Billing Export 文件](https://cloud.google.com/billing/docs/how-to/export-data-bigquery)
- [BigQuery 計價](https://cloud.google.com/bigquery/pricing)
- [google-cloud-bigquery Python 用戶端](https://cloud.google.com/python/docs/reference/bigquery/latest)
