# GitHub Actions → GCP CI/CD 部署設置

本指南說明如何設置 GitHub Actions 自動部署到 GCP。

---

## 架構

```
GitHub Actions (Ubuntu)
    ↓
Workload Identity Federation (WIF)
    ↓ OAuth 2.0 Token Exchange
Google Cloud (certimate-titi)
    ├─ Cloud Build (Docker image)
    ├─ Artifact Registry (Push image)
    ├─ Cloud Run (Deploy service)
    └─ Cloud SQL (Database)
```

---

## 設置步驟

### Step 1: 建立 GCP Service Account

```bash
# 1. 設置變數
export PROJECT_ID="certimate-titi"
export SA_NAME="github-actions"

# 2. 建立 Service Account
gcloud iam service-accounts create ${SA_NAME} \
  --display-name="GitHub Actions CI/CD" \
  --project=${PROJECT_ID}

# 3. 取得 Service Account email
SA_EMAIL=$(gcloud iam service-accounts list \
  --filter="displayName:GitHub" \
  --format='value(email)' \
  --project=${PROJECT_ID})
echo "Service Account: $SA_EMAIL"
```

### Step 2: 授予必要的 IAM 權限

```bash
# Cloud Run Deploy
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Artifact Registry Push
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# Cloud Build Submit
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudbuild.builds.editor"

# Cloud SQL
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client"

# Service Account User (for Cloud Run)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

# Firebase Deploy
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/firebase.admin"
```

### Step 3: 設置 Workload Identity Federation (WIF)

這允許 GitHub Actions 無需存儲長期憑證，直接請求短期 access token。

```bash
# 1. 啟用 STS API
gcloud services enable sts.googleapis.com \
  --project=${PROJECT_ID}

# 2. 建立 Workload Identity Provider
gcloud iam workload-identity-pools create "github-pool" \
  --project=${PROJECT_ID} \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 3. 取得 Workload Identity Provider
WIP=$(gcloud iam workload-identity-pools describe "github-pool" \
  --project=${PROJECT_ID} \
  --location="global" \
  --format='value(name)')

# 4. 建立 OIDC Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project=${PROJECT_ID} \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.aud=assertion.aud" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 5. 將 Workload Identity 與 Service Account 綁定
gcloud iam service-accounts add-iam-policy-binding ${SA_EMAIL} \
  --project=${PROJECT_ID} \
  --role="roles/iam.workloadIdentityUser" \
  --condition=None \
  --member="principalSet://iam.googleapis.com/${WIP}/attribute.repository/certimate-titi/certimate"
```

### Step 4: 取得 GitHub 所需的 Secrets 值

```bash
# 1. 取得 WIF Provider
WIP=$(gcloud iam workload-identity-pools describe "github-pool" \
  --project=${PROJECT_ID} \
  --location="global" \
  --format='value(name)')

WIP_PROVIDER="${WIP}/providers/github-provider"
echo "WIF_PROVIDER: $WIP_PROVIDER"

# 2. 取得 Service Account Email
echo "WIF_SERVICE_ACCOUNT: $SA_EMAIL"
```

### Step 5: 建立 Firebase Service Account 金鑰

```bash
# 建立 key
gcloud iam service-accounts keys create firebase-sa-key.json \
  --iam-account=${SA_EMAIL} \
  --project=${PROJECT_ID}

# 轉換為 base64（用於 GitHub Secret）
cat firebase-sa-key.json | base64 -w 0
```

### Step 6: 在 GitHub 中設定 Secrets

進入 GitHub Repository → Settings → Secrets and variables → Actions，新增以下 secrets：

| Secret Name | 值 | 取得方式 |
|-------------|-----|---------|
| `WIF_PROVIDER` | `projects/123456/locations/global/workloadIdentityPools/github-pool/providers/github-provider` | Step 4 |
| `WIF_SERVICE_ACCOUNT` | `github-actions@certimate-titi.iam.gserviceaccount.com` | Step 4 |
| `FIREBASE_SERVICE_ACCOUNT` | Base64 encoded JSON key | Step 5 |
| `DB_PASSWORD` | `CertiMate2026!` | 已知 |
| `JWT_SECRET_KEY` | `certimate-production-jwt-secret-2026` | 已知 |
| `GOOGLE_CLIENT_ID` | `63018063271-fu1r2h37b3ttqr9uu5bthas2blt94c7l.apps.googleusercontent.com` | 已知 |
| `SMTP_USER` | `son731202@gmail.com` | 已知 |
| `SMTP_PASSWORD` | `ptmqwgqcphubajbr` | 已知 |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | `AIzaSyA5LshjGNrYxSOabPqaxB_EQb-AMjd-6ks` | 已知 |

---

## 觸發部署

### 自動觸發
部署會在以下情況自動觸發：
- ✅ 推送到 `main` 分支
- ✅ 推送到 `production` 分支

### 手動觸發
在 GitHub UI 中：
1. 進入 Actions 標籤
2. 選擇「Deploy to GCP」
3. 點擊「Run workflow」

### 查看部署日誌
1. 進入 Actions 標籤
2. 選擇最新的「Deploy to GCP」執行
3. 查看各個 step 的日誌

---

## 部署流程（自動）

1. **代碼簽入** → GitHub 檢測到 push
2. **啟動 Workflow** → Actions 開始執行
3. **驗證身份** → Workload Identity Federation 交換 token
4. **建置後端** → Cloud Build 建置 Docker image
5. **推送映像** → Artifact Registry 存儲映像
6. **部署服務** → Cloud Run 部署新版本
7. **Seed Demo** → 建立 demo 帳號
8. **建置前端** → Next.js 靜態導出
9. **部署前端** → Firebase Hosting 上線
10. **Smoke Test** → 驗證所有端點正常
11. **摘要報告** → Actions 彙總結果

---

## 常見問題

### Q1: WIF 驗證失敗 — "permission denied"

**原因**：Service Account 缺少必要權限  
**解決**：重新執行 Step 2（授予 IAM 角色）

```bash
# 驗證權限
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${SA_EMAIL}"
```

### Q2: "Artifact Repository not found"

**原因**：Artifact Registry 尚未建立  
**解決**：
```bash
gcloud artifacts repositories create certimate \
  --repository-format=docker \
  --location=asia-east1 \
  --project=${PROJECT_ID}
```

### Q3: Cloud Run deployment 超時

**原因**：容器啟動失敗（通常是環境變數問題）  
**解決**：查看 Cloud Run 日誌
```bash
gcloud run services logs read certimate-titi --region=asia-east1 --limit=50
```

### Q4: Firebase 部署失敗

**原因**：Firebase Service Account 金鑰格式錯誤  
**解決**：確認 base64 編碼無誤
```bash
# 重新生成金鑰
gcloud iam service-accounts keys create firebase-sa-key.json \
  --iam-account=${SA_EMAIL}

# 正確的 base64 編碼
cat firebase-sa-key.json | base64 -w 0 | xclip -selection clipboard
```

---

## 監控與故障排查

### GitHub Actions 日誌

每次部署都會詳細記錄，包括：
- ✅ 各步驟執行時間
- ✅ 成功/失敗狀態
- ✅ 錯誤訊息與堆棧追蹤

### GCP 日誌

```bash
# Cloud Run 日誌
gcloud run services logs read certimate-titi --region=asia-east1 --follow

# Cloud Build 日誌
gcloud builds log <BUILD_ID> --stream

# Artifact Registry
gcloud artifacts docker images list asia-east1-docker.pkg.dev/certimate-titi/certimate
```

---

## 回滾

如果新部署有問題，快速回滾：

```bash
# 查看部署歷史
gcloud run revisions list --service=certimate-titi --region=asia-east1

# 回滾到上個版本
PREVIOUS=$(gcloud run revisions list --service=certimate-titi --region=asia-east1 \
  --format='value(name)' --limit=2 | tail -1)

gcloud run services update-traffic certimate-titi \
  --to-revisions=$PREVIOUS=100 \
  --region=asia-east1
```

---

## 成本監控

每次部署約需：
- Cloud Build：$0.01（10 分鐘 @ $0.06/min）
- Cloud Run：最少 $0.01/月（free tier）
- Firebase Hosting：$0（free tier）

**預期月費**：~$0.30（部署 30 次）+ $7.67（Cloud SQL）= **~$8/月**

---

## 下一步

1. ✅ 執行上述設置步驟
2. ✅ 在 GitHub 中配置 Secrets
3. ✅ 推送到 main 分支觸發自動部署
4. ✅ 監控 Actions 日誌確認部署成功
5. ✅ 訪問 https://certimate-titi.web.app 驗證

有任何問題？查看 GitHub Actions 日誌或 GCP Console！
