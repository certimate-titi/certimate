# CI/CD 部署說明 — GCP Billing Export 集成

**最後更新**: 2026-04-17

## 🚀 部署流程

當代碼推送到 `main` 或 `production` 分支時，GitHub Actions 會自動觸發部署：

### 部署步驟

1. **認證** — 使用 Workload Identity Provider 認證到 GCP
2. **上傳資源** — 考古題 JSON + Prompt 模板上傳到 GCS
3. **構建映像** — Docker 映像構建並推送到 Artifact Registry
4. **部署後端** — 部署到 Cloud Run + 設置環境變數
5. **部署前端** — Next.js 構建 + Firebase Hosting
6. **烟雾測試** — 驗證關鍵 API 端點
7. **通知** — 部署完成通知

## 🔧 GCP Billing Export 配置

### 開發模式（預設）

```yaml
GCP_BILLING_MODE=fake                    # 返回 stub 資料（不調用 BigQuery）
GCP_PROJECT_ID=certimate-titi
GCP_BILLING_EXPORT_DATASET=billing_export
GCP_BILLING_EXPORT_TABLE=gcp_billing_export_v1
```

✅ **安全**：不依賴外部服務，CI/CD 快速完成

### 生產模式（手動啟用）

要在 Cloud Run 上啟用真實模式：

```bash
# 方案 A: 使用 Workload Identity（推薦）
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --service-account=certimate-billing@certimate-titi.iam.gserviceaccount.com \
  --region=asia-east1

# 方案 B: 掛載 Service Account Key（不推薦，安全風險）
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --set-env-vars GCP_BQ_CREDENTIALS_PATH=/var/secrets/gcp-billing/key.json \
  --region=asia-east1
```

## 📊 部署檢查清單

| 項目 | 狀態 | 說明 |
|------|------|------|
| CI/CD 配置 | ✅ | `deploy-gcp.yml` 已配置 GCP Billing 環境變數 |
| 開發模式 | ✅ | 自動使用 `GCP_BILLING_MODE=fake` |
| 文檔 | ✅ | `GCP_BILLING_EXPORT_SETUP.md` 提供升級指南 |
| 煙霧測試 | ✅ | `smoke-test.sh` 驗證 API 端點 |
| 真實模式 | ⏳ | 待手動啟用（需要 Service Account key） |

## 🔐 環境變數管理

### CI/CD 設定（自動）

這些變數在 **deploy-gcp.yml** 中自動設置：

```yaml
GCP_PROJECT_ID: certimate-titi
FRONTEND_URL: https://certimate-titi.web.app
```

### Cloud Run 機密（需要設置）

如需啟用真實模式，需要在 Cloud Run 上手動配置：

```bash
# 方案 1: Workload Identity（推薦，無需存儲密鑰）
gcloud run services update certimate-api \
  --service-account=certimate-billing@certimate-titi.iam.gserviceaccount.com

# 方案 2: Secret Manager（存儲敏感信息）
gcloud secrets create gcp-billing-key \
  --data-file=path/to/service-account.json

gcloud run services update certimate-api \
  --update-secrets GCP_BQ_CREDENTIALS_PATH=gcp-billing-key:latest
```

## 🐛 故障排除

### 部署失敗

```bash
# 1. 檢查 GitHub Actions 日誌
#    https://github.com/certimate/certimate/actions

# 2. 查看 Cloud Run 部署日誌
gcloud run services logs read certimate-api --limit=100

# 3. 查看特定錯誤
gcloud run services logs read certimate-api --limit=50 | grep -i "error\|billing"
```

### API 回傳 503（GCP Billing 不可用）

```bash
# 1. 驗證環境變數
gcloud run services describe certimate-api \
  --format="value(spec.template.spec.containers[0].env)"

# 2. 確認 GCP_BILLING_MODE 設置
echo $GCP_BILLING_MODE  # 應為 "real" 或 "fake"

# 3. 驗證 Service Account 權限
gcloud projects get-iam-policy certimate-titi \
  --flatten="bindings[].members" | grep certimate-billing
```

## 📈 監控

### 部署成功指標

```bash
# 檢查 Cloud Run 服務狀態
gcloud run services describe certimate-api --region=asia-east1

# 測試 API
curl https://certimate-titi-*.run.app/api/v1/admin/cost/summary \
  -H "Authorization: Bearer <token>"
```

### 日誌查詢

```bash
# 查看最近部署日誌
gcloud run services logs read certimate-api --limit=50

# 監控特定功能
gcloud run services logs read certimate-api --limit=100 | grep "GCP Billing"

# 實時日誌流（需要 gcloud beta）
gcloud beta run services logs stream certimate-api --region=asia-east1
```

## 🔄 部署工作流程

### 本地開發 → GitHub → Cloud Run

```
1. 本地開發
   └─ git commit 到本地分支

2. 推送到 GitHub
   └─ git push origin feature-branch

3. 建立 Pull Request (PR)
   └─ 自動運行 linting + 單元測試（若有配置）

4. PR 合併到 main/production
   └─ 自動觸發 deploy-gcp.yml

5. GitHub Actions 執行
   ├─ 構建 Docker 映像
   ├─ 推送到 Artifact Registry
   ├─ 部署到 Cloud Run
   ├─ 部署前端到 Firebase
   ├─ 運行煙霧測試
   └─ 發送部署完成通知

6. 部署完成
   └─ API 在 https://certimate-titi-*.run.app 可用
```

## 📝 部署後檢查

```bash
#!/bin/bash
# 部署驗證腳本

BACKEND_URL="https://certimate-titi-*.run.app"

# 1. API 健康檢查
echo "✓ 檢查 API 狀態..."
curl -s "${BACKEND_URL}/api/v1/health" || echo "❌ API 不可用"

# 2. GCP Billing Export
echo "✓ 檢查 GCP Billing..."
curl -s "${BACKEND_URL}/api/v1/admin/cost/gcp/services" \
  -H "Authorization: Bearer <token>" | jq '.total_usd'

# 3. 前端應用
echo "✓ 檢查前端..."
curl -s "https://certimate-titi.web.app" | grep -q "CertiMate" && echo "✓ 前端正常"

# 4. 考古題資料
echo "✓ 檢查考古題載入..."
gsutil ls gs://certimate-titi-data/historical_questions/ | wc -l
```

## 🎯 下一步（可選優化）

### 1. 啟用真實 GCP Billing
```bash
gcloud run services update certimate-api \
  --set-env-vars GCP_BILLING_MODE=real \
  --service-account=certimate-billing@certimate-titi.iam.gserviceaccount.com
```

### 2. 設置部署通知
- Slack 集成
- Email 警報
- PagerDuty 整合

### 3. 監控告警
- 部署失敗告警
- API 可用性監控
- 成本異常告警

## 📚 相關文件

- 📋 [GCP Billing Export 設定指南](./GCP_BILLING_EXPORT_SETUP.md)
- 📄 [Billing Export 實現總結](./BILLING_EXPORT_COMPLETION.md)
- 🔧 [部署工作流設定](./.github/workflows/deploy-gcp.yml)
- ✅ [煙霧測試腳本](./smoke-test.sh)

## 常見問題

**Q: 為何 CI/CD 中使用 fake 模式而非 real 模式？**  
A: 安全性考量。fake 模式返回 stub 資料，無需 GCP credentials，部署更快。真實模式需要手動配置 Service Account，確保安全無誤後再在生產環境啟用。

**Q: 如何回滾部署？**  
A: Cloud Run 版本管理自動保留最近 10 個版本。使用：
```bash
gcloud run services update-traffic certimate-api \
  --to-revisions=<revision-id>=100
```

**Q: 部署失敗如何解決？**  
A: 檢查 GitHub Actions 日誌 → 查看 Cloud Run 服務日誌 → 驗證環境變數。詳見故障排除章節。
