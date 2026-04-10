# CertiMate GCP 部署指南

**最後更新**：2026-04-10  
**狀態**：準備就緒 ✅

---

## 快速開始

### 在本機執行完整部署

```bash
# 1. 確認已登入 GCP
gcloud auth login
gcloud config set project certimate-titi

# 2. 部署後端 + 前端
./deploy.sh all

# 3. 驗證部署
./smoke-test.sh
```

---

## 環境資訊

| 項目 | 值 |
|------|-----|
| **GCP Project ID** | `certimate-titi` |
| **Region** | `asia-east1` |
| **Backend Service** | Cloud Run: `certimate-titi` |
| **Frontend** | Firebase Hosting: `certimate-titi.web.app` |
| **Database** | Cloud SQL: `certimate-db` (PostgreSQL 15) |
| **Container Registry** | Artifact Registry: `asia-east1-docker.pkg.dev/certimate-titi/certimate` |

---

## 部署步驟

### Step 1: 後端部署（Cloud Run）

```bash
cd /home/user/certimate

# 取得 commit hash
SHORT_SHA=$(git rev-parse --short HEAD)

# Cloud Build：build image + push to Artifact Registry
gcloud builds submit --config cloudbuild.yaml \
  --substitutions="_SERVICE_NAME=certimate-titi,_REGION=asia-east1,SHORT_SHA=$SHORT_SHA"
```

**注意**：Cloud Build Step 3 (deploy) 會因為 env vars 缺失而失敗。需要手動部署：

```bash
gcloud run deploy certimate-titi \
  --image asia-east1-docker.pkg.dev/certimate-titi/certimate/certimate-titi:$SHORT_SHA \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 2 \
  --concurrency 80 \
  --timeout 300 \
  --add-cloudsql-instances certimate-titi:asia-east1:certimate-db \
  --set-env-vars \
    "DATABASE_URL=postgresql+psycopg://postgres:CertiMate2026!@/certimate?host=/cloudsql/certimate-titi:asia-east1:certimate-db,\
JWT_SECRET_KEY=certimate-production-jwt-secret-2026,\
FRONTEND_URL=https://certimate-titi.web.app,\
FIREBASE_PROJECT_ID=certimate-titi,\
GOOGLE_CLIENT_ID=63018063271-fu1r2h37b3ttqr9uu5bthas2blt94c7l.apps.googleusercontent.com,\
SMTP_HOST=smtp.gmail.com,\
SMTP_USER=son731202@gmail.com,\
SMTP_PASSWORD=ptmqwgqcphubajbr"
```

#### Seed Demo 帳號

部署後，建立 demo 帳號供測試使用：

```bash
curl -X POST https://certimate-titi-63018063271.asia-east1.run.app/api/v1/auth/seed-demo

# 預期回應：
# {"message":"Demo account created"}
# or
# {"message":"Demo account already exists"}

# Demo 帳號：
# Email: admin@certimate.com
# Password: admin123
```

---

### Step 2: 前端部署（Firebase Hosting）

```bash
cd frontend

# 重要：用環境變數覆蓋 .env.local，否則 build 會指向 localhost
NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1 npm run build

# 驗證：確保 build 結果中沒有 localhost
grep -roh 'localhost:8000' out/_next/static/chunks/ 2>/dev/null
# 應該無輸出！如果有，表示 env var 覆蓋失敗

# 部署
firebase deploy --only hosting
```

**預期結果**：
```
Deploy complete!

Project Console: https://console.firebase.google.com/project/certimate-titi
Hosting URL: https://certimate-titi.web.app
```

---

### Step 3: Smoke Test

所有部署完成後，驗證服務正常：

```bash
./smoke-test.sh

# 預期結果：8/8 passed ✅
```

---

## 常見問題排查

### Q1: Cloud Build 失敗 `SHORT_SHA` 為空

**原因**：非 git push trigger 觸發  
**解決**：
```bash
SHORT_SHA=$(git rev-parse --short HEAD)
gcloud builds submit --config cloudbuild.yaml \
  --substitutions="_SERVICE_NAME=certimate-titi,_REGION=asia-east1,SHORT_SHA=$SHORT_SHA"
```

### Q2: Container 啟動失敗 — `ModuleNotFoundError`

**原因**：dependencies 未正確安裝  
**解決**：
```bash
# 檢查 backend/Dockerfile
cat backend/Dockerfile

# 確保 .venv/lib/python3.11/site-packages 包含所有套件
docker run --rm \
  asia-east1-docker.pkg.dev/certimate-titi/certimate/certimate-titi:latest \
  python -c "import psycopg; print('✅ psycopg OK')"
```

### Q3: 前端仍然指向 localhost

**原因**：`.env.local` 覆蓋了 env var  
**解決**：
```bash
# 確認 .env.local 中沒有 NEXT_PUBLIC_API_URL，或移除它
rm frontend/.env.local

# 重新 build
NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1 npm run build

# 驗證
grep -r "localhost:8000" out/ 2>/dev/null || echo "✅ No localhost references"
```

### Q4: CORS 錯誤 — `Failed to fetch`

**原因**：後端未包含前端 origin  
**解決**：
```bash
# 檢查 backend/app/core/config.py 的 ALLOWED_ORIGINS
gcloud run services describe certimate-titi --region=asia-east1 \
  --format='yaml(spec.template.spec.containers[0].env)'

# 更新（如果需要）
gcloud run deploy certimate-titi --region=asia-east1 \
  --set-env-vars "ALLOWED_ORIGINS=https://certimate-titi.web.app"
```

### Q5: Smoke Test 失敗 — 間歇性 502 Bad Gateway

**原因**：Cloud Run cold start（min-instances=0）  
**解決**：
```bash
# 暫時增加 min-instances
gcloud run deploy certimate-titi --region=asia-east1 \
  --min-instances 1

# 或忽略（容器啟動後 1-2 秒即可恢復）
```

---

## 環境變數清單

### Cloud Run (Backend)

| 變數 | 值 |
|------|-----|
| `DATABASE_URL` | `postgresql+psycopg://postgres:CertiMate2026!@/certimate?host=/cloudsql/certimate-titi:asia-east1:certimate-db` |
| `JWT_SECRET_KEY` | `certimate-production-jwt-secret-2026` |
| `FRONTEND_URL` | `https://certimate-titi.web.app` |
| `FIREBASE_PROJECT_ID` | `certimate-titi` |
| `GOOGLE_CLIENT_ID` | `63018063271-fu1r2h37b3ttqr9uu5bthas2blt94c7l.apps.googleusercontent.com` |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_USER` | `son731202@gmail.com` |
| `SMTP_PASSWORD` | `ptmqwgqcphubajbr` |

### Frontend (.env.local or build-time)

```bash
NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyA5LshjGNrYxSOabPqaxB_EQb-AMjd-6ks
```

---

## CI/CD 整合（自動部署）

### GitHub Actions 範例

```yaml
name: Deploy to GCP

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          project_id: certimate-titi
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          export_default_credentials: true
      
      - name: Build & Deploy Backend
        run: |
          SHORT_SHA=$(git rev-parse --short HEAD)
          gcloud builds submit --config cloudbuild.yaml \
            --substitutions="_SERVICE_NAME=certimate-titi,_REGION=asia-east1,SHORT_SHA=$SHORT_SHA"
      
      - name: Deploy Frontend
        run: |
          cd frontend
          NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1 npm run build
          firebase deploy --token ${{ secrets.FIREBASE_TOKEN }} --only hosting
      
      - name: Smoke Test
        run: ./smoke-test.sh
```

---

## 監控與日誌

### 查看 Cloud Run 日誌

```bash
# 即時日誌
gcloud run services logs read certimate-titi --region=asia-east1 --limit=50 --follow

# 查看最近 100 行
gcloud run services logs read certimate-titi --region=asia-east1 --limit=100
```

### 檢查 Cloud Run 服務狀態

```bash
gcloud run services describe certimate-titi --region=asia-east1
```

### Firebase Hosting 日誌

```bash
firebase hosting:channel:list
firebase hosting:channel:deploy preview-123  # Deploy to preview channel
```

---

## 回滾與版本管理

### 查看部署歷史

```bash
gcloud run revisions list --service certimate-titi --region=asia-east1
```

### 回滾到上個版本

```bash
PREVIOUS_REVISION=$(gcloud run revisions list --service certimate-titi --region=asia-east1 \
  --format='value(name)' --limit=2 | tail -1)

gcloud run services update-traffic certimate-titi \
  --to-revisions $PREVIOUS_REVISION=100 \
  --region=asia-east1
```

---

## 安全檢查清單

- [ ] 環境變數已設置（DATABASE_URL、JWT_SECRET_KEY 等）
- [ ] Cloud SQL 密碼已安全存儲（Secret Manager）
- [ ] Cloud Run 設置 `--allow-unauthenticated` 只限 public endpoints
- [ ] CORS 已正確配置（僅允許 certimate-titi.web.app）
- [ ] Database 連線已加密（Cloud SQL 代理）
- [ ] Firebase Hosting 已啟用 HTTPS（預設）
- [ ] Smoke Test 8/8 passed ✅

---

## 支持

如需幫助：
1. 查看 Cloud Run 日誌：`gcloud run services logs read certimate-titi --limit=50`
2. 檢查 Artifact Registry image 存在：`gcloud artifacts docker images list asia-east1-docker.pkg.dev/certimate-titi/certimate`
3. 測試 database 連線：`gcloud sql connect certimate-db --user=postgres`
