# GCP Billing Export 啟用與整合手冊

**文件編號**: INFRA-gcp-billing-export
**產出角色**: 雲端工程師（CTO 技術線）
**產出日期**: 2026-04-14
**狀態**: Draft v1（需 Simon 在 GCP Console 手動執行）
**對應 Feature**: 33 — 成本監控中心
**風險等級**: 🟡 涉及 GCP Billing Account 權限

---

## ⚠️ 重要前置提醒

本手冊的 **第 1-3 節必須在 GCP Console 手動執行**，Claude 無法代為操作（涉及 Billing Account 級別權限與敏感憑證生成）。請依順序執行並回報每個檢核點的結果。

操作前請確認：
- [ ] 您有 CertiMate GCP 專案的 **Billing Account Administrator** 或 **Billing Account Costs Manager** 權限
- [ ] 您有 CertiMate GCP 專案的 **Owner** 或 **IAM Admin** 權限
- [ ] 您已經備份現有 `.env` 檔案

---

## 1. 啟用 BigQuery Billing Export（GCP Console 操作）

### 1.1 建立 BigQuery Dataset
1. 前往 **BigQuery Console** → 選擇 CertiMate 專案
2. 點擊專案旁的 `⋮` → **Create dataset**
3. 填入：
   - **Dataset ID**: `billing_export`
   - **Location type**: Multi-region → `asia`（或選擇與 Cloud Run 同區，節省 egress）
   - **Default table expiration**: 不設定（帳單資料需保留）
   - **Encryption**: Google-managed encryption key（預設即可）
4. 點擊 **Create Dataset**

### 1.2 啟用 Billing Export
1. 前往 **Billing Console**（`https://console.cloud.google.com/billing`）
2. 選擇 CertiMate 使用的 **Billing Account**
3. 左側選單 → **Billing export**
4. **Standard usage cost** 區塊 → 點擊 **Edit settings**
5. 設定：
   - **Project**: CertiMate GCP 專案
   - **Dataset**: `billing_export`（剛建立的）
6. 點擊 **Save**
7. 回到頁面確認狀態顯示為 **"Enabled"**

### 1.3 等待首批資料（重要）
- **首次啟用後約 4-24 小時**才會有第一批資料寫入
- 資料每日 UTC 00:00 更新，延遲約 4-8 小時
- **本機開發階段**可先用固定假資料測試，等 export 就緒後再接真實 BQ

### 1.4 驗證資料已進入 BQ
```sql
-- 在 BigQuery Console 執行
SELECT
  service.description AS service_name,
  SUM(cost) AS total_cost_usd,
  currency
FROM `<PROJECT_ID>.billing_export.gcp_billing_export_v1_*`
WHERE DATE(_PARTITIONTIME) = CURRENT_DATE() - 1
GROUP BY service_name, currency
ORDER BY total_cost_usd DESC
LIMIT 10;
```
預期：看到 Cloud Run、Cloud SQL、BigQuery 等服務名稱與金額。

---

## 2. 建立服務帳號與憑證（GCP Console 操作）

### 2.1 建立服務帳號
1. 前往 **IAM & Admin** → **Service accounts**
2. 點擊 **Create service account**
3. 填入：
   - **Name**: `cost-monitor-bq-reader`
   - **ID**: `cost-monitor-bq-reader`
   - **Description**: "CertiMate Feature 33 成本監控中心 BigQuery 讀取服務帳號"
4. 點擊 **Create and continue**

### 2.2 授予最小權限（極重要）
**只授予以下兩個角色**，不可給 Owner / Editor：
- `BigQuery Data Viewer`（`roles/bigquery.dataViewer`）
- `BigQuery Job User`（`roles/bigquery.jobUser`）

完成後點擊 **Done**。

### 2.3 限定資源範圍（Condition）
1. 在剛建立的服務帳號頁面點擊 **Permissions**
2. 編輯 `BigQuery Data Viewer` → 加上 IAM Condition：
   ```
   resource.type == "bigquery.googleapis.com/Dataset"
   && resource.name == "projects/<PROJECT_ID>/datasets/billing_export"
   ```
   這確保此帳號**只能**讀 `billing_export` dataset，不能看其他業務資料。

### 2.4 產生金鑰（JSON）
1. 在服務帳號頁面 → **Keys** → **Add key** → **Create new key**
2. 類型選 **JSON** → **Create**
3. 瀏覽器會下載一個 JSON 檔 — **這是敏感憑證，不可 commit**
4. 將檔案暫存至本地不進 git 的路徑，例如 `~/.gcp/cost-monitor-bq-reader.json`

---

## 3. 將憑證放入環境

### 3.1 本地開發（.env）
```bash
# 新增至 backend/.env
GCP_PROJECT_ID=certimate-titi
GCP_BILLING_EXPORT_DATASET=billing_export
GCP_BQ_CREDENTIALS_PATH=/Users/simon/.gcp/cost-monitor-bq-reader.json
```

### 3.2 Production（Cloud Run）
**使用 GCP Secret Manager，不要放 .env**：

```bash
# 1. 建立 secret
gcloud secrets create cost-monitor-bq-credentials \
    --data-file=cost-monitor-bq-reader.json \
    --project=certimate-titi

# 2. 授予 Cloud Run 執行身份讀取權限
gcloud secrets add-iam-policy-binding cost-monitor-bq-credentials \
    --member="serviceAccount:<CLOUD_RUN_RUNTIME_SA>@certimate-titi.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=certimate-titi

# 3. Cloud Run 部署時掛載 secret 為檔案
gcloud run services update certimate-backend \
    --update-secrets=/secrets/bq-credentials.json=cost-monitor-bq-credentials:latest \
    --set-env-vars=GCP_BQ_CREDENTIALS_PATH=/secrets/bq-credentials.json
```

### 3.3 .gitignore 檢查
確認以下 pattern 已在專案根 `.gitignore`：
```
*.json.credentials
*-credentials.json
cost-monitor-bq-reader.json
.gcp/
```

---

## 4. 應用層整合（程式碼交付）

### 4.1 Service 層骨架
見 `backend/app/services/gcp_billing_service.py`（本次交付）。

### 4.2 查詢快取策略
- **快取粒度**：整份「服務分類」結果 + 「30 天趨勢」結果各一份
- **TTL**：1 小時
- **快取儲存**：本地記憶體（`functools.lru_cache` 或 `cachetools.TTLCache`）
- **理由**：BQ 查詢本身會產生費用（免費 tier 1 TB/月），快取可降低 99% 查詢量

### 4.3 降級處理
若 BQ 查詢失敗（憑證過期、API 異常、quota 超限）：
- Router 回傳 `503 Service Unavailable` + `code: "GCP_BILLING_TEMPORARILY_UNAVAILABLE"`
- 前端顯示「GCP 帳單資料暫時無法取得，其他供應商資料照常顯示」
- 不可因 GCP 查詢失敗而讓整個成本監控頁面掛掉

---

## 5. 檢核清單（Simon 親自執行後回報）

執行完成後請逐項回覆給 CTO：

### GCP Console 操作
- [ ] 1.1 已建立 BigQuery dataset `billing_export`，location: `asia`
- [ ] 1.2 已啟用 Billing Export，頁面狀態為 Enabled
- [ ] 1.3 已記下首次啟用時間：________（預計 24h 後驗證）
- [ ] 1.4 24h 後已驗證 BQ 中有帳單資料（回報服務數量與總金額）

### 服務帳號
- [ ] 2.1 已建立 `cost-monitor-bq-reader`
- [ ] 2.2 僅授予 `BigQuery Data Viewer` + `BigQuery Job User`（**不是 Owner**）
- [ ] 2.3 IAM Condition 已限定在 `billing_export` dataset
- [ ] 2.4 已下載 JSON 金鑰並存放於 `~/.gcp/`（**未 commit**）

### 憑證配置
- [ ] 3.1 本地 `backend/.env` 已加入三個環境變數
- [ ] 3.2 Production 尚未執行（等上線前執行 Secret Manager 步驟）
- [ ] 3.3 `.gitignore` 已確認

---

## 6. 成本預估

| 項目 | 預估月成本 |
|------|-----------|
| Billing Export 寫入 BQ | **免費**（Google 免費提供） |
| BQ 儲存（帳單資料） | ~$0.02（每月約 1 GB） |
| BQ 查詢（有 1 小時快取） | ~$0.00（遠低於免費 tier 1 TB） |
| **總計** | **< $0.05/月** |

→ 啟用此功能對 GCP 帳單影響可忽略。

---

## 7. 常見問題

### Q1: 啟用後 24 小時沒資料？
- 檢查 Billing Console 的 Export 狀態是否為 Enabled
- 檢查選擇的 Dataset 是否正確（避免選到其他專案的 dataset）
- 確認 Billing Account 本月有實際消費（沒消費就沒資料）

### Q2: 服務帳號沒權限查 BQ？
- 確認角色是否掛在**服務帳號本身**，不是 Billing Account
- 等 5 分鐘讓權限傳播

### Q3: Production 部署時找不到憑證？
- 確認 Cloud Run 的 Runtime Service Account 已授權讀 Secret
- 確認 `--update-secrets` 掛載路徑與 `GCP_BQ_CREDENTIALS_PATH` 一致

---

## 8. 給 CTO 的三句話

1. 第 1-2 節必須 **Simon 在 GCP Console 手動執行**，Claude 無法代勞
2. 服務帳號**只給 BigQuery Data Viewer + Job User**，絕不可給 Owner（最小權限原則）
3. 首次啟用後 **24 小時**才會有資料，期間可用固定假資料做開發與測試
