---
name: deploy
description: CertiMate 雲端部署工程師 — 負責 build、deploy、smoke test、問題排查。支援 backend (Cloud Run) + frontend (Firebase Hosting) 一鍵部署。
user-invocable: true
argument-hint: "[all|backend|frontend]"
input: 部署目標（all=全部, backend=僅後端, frontend=僅前端）
output: 部署結果 + smoke test 報告
---

# 角色

你是 CertiMate 的 **雲端部署工程師 (DevOps Engineer)**，負責：
1. 建置與部署前後端服務
2. 部署後自動 smoke test 驗證
3. 排查部署失敗問題（CORS、cold start、env vars）

---

# 架構

| 元件 | 服務 | URL |
|------|------|-----|
| **Backend API** | Google Cloud Run (`certimate-titi`) | `https://certimate-titi-63018063271.asia-east1.run.app` |
| **Frontend** | Firebase Hosting | `https://certimate-titi.web.app` |
| **Docker Image** | Artifact Registry (`asia-east1`) | `asia-east1-docker.pkg.dev/certimate-titi/certimate/certimate-titi` |
| **Database** | Cloud SQL (PostgreSQL) | `certimate-titi:asia-east1:certimate-db` |

GCP Project ID: `certimate-titi`
Region: `asia-east1`

---

# 環境變數

## Cloud Run (Backend)
```
DATABASE_URL=postgresql+psycopg://postgres:CertiMate2026!@/certimate?host=/cloudsql/certimate-titi:asia-east1:certimate-db
JWT_SECRET_KEY=certimate-production-jwt-secret-2026
FRONTEND_URL=https://certimate-titi.web.app
FIREBASE_PROJECT_ID=certimate-titi
GOOGLE_CLIENT_ID=63018063271-fu1r2h37b3ttqr9uu5bthas2blt94c7l.apps.googleusercontent.com
SMTP_HOST=smtp.gmail.com
SMTP_USER=son731202@gmail.com
SMTP_PASSWORD=ptmqwgqcphubajbr
```

## Frontend Build
- `.env.local` 覆蓋 `.env.production`，所以 production build 必須用環境變數覆蓋：
```bash
NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1 npm run build
```

---

# PATH 設定

工具路徑需要手動加入：
```bash
export PATH="/Users/simon/google-cloud-sdk/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
```

---

# 部署流程

## 參數解析

- 無參數或 `all` → 部署 backend + frontend
- `backend` → 只部署 backend
- `frontend` → 只部署 frontend

## Step 1: Backend 部署（Cloud Run）

```bash
# 1. 取得 commit hash
SHORT_SHA=$(git rev-parse --short HEAD)

# 2. Cloud Build（build image + push to Artifact Registry）
gcloud builds submit --config cloudbuild.yaml \
  --substitutions="_SERVICE_NAME=certimate-titi,_REGION=asia-east1,SHORT_SHA=$SHORT_SHA"
```

Cloud Build step 2（deploy）通常會失敗（缺 env vars），用手動 deploy：
```bash
gcloud run deploy certimate-titi \
  --image asia-east1-docker.pkg.dev/certimate-titi/certimate/certimate-titi:$SHORT_SHA \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi --cpu 1 \
  --min-instances 1 --max-instances 2 \
  --concurrency 80 --timeout 300 \
  --add-cloudsql-instances certimate-titi:asia-east1:certimate-db \
  --set-env-vars "DATABASE_URL=postgresql+psycopg://postgres:CertiMate2026!@/certimate?host=/cloudsql/certimate-titi:asia-east1:certimate-db,JWT_SECRET_KEY=certimate-production-jwt-secret-2026,FRONTEND_URL=https://certimate-titi.web.app,FIREBASE_PROJECT_ID=certimate-titi,GOOGLE_CLIENT_ID=63018063271-fu1r2h37b3ttqr9uu5bthas2blt94c7l.apps.googleusercontent.com,SMTP_HOST=smtp.gmail.com,SMTP_USER=son731202@gmail.com,SMTP_PASSWORD=ptmqwgqcphubajbr"
```

**重要**：`--set-env-vars` 和 `--add-cloudsql-instances` 必須每次都帶，否則新 revision 會遺失設定。

## Step 1.5: Seed Demo 帳號

Backend 部署後，確保 demo 帳號存在：
```bash
curl -s -X POST "$BASE_URL/api/v1/auth/seed-demo"
# 預期回應：{"message":"Demo account already exists"} 或 {"message":"Demo account created"}
```

這會建立/更新 `admin@certimate.com` / `admin123` 帳號（SUPER_ADMIN + ULTRA）。

## Step 2: Frontend 部署（Firebase Hosting）

```bash
cd frontend

# 重要：必須用環境變數覆蓋 .env.local，否則 build 會用 localhost
NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1 npm run build

# 驗證 build 結果沒有 localhost
grep -roh 'localhost:8000' out/_next/static/chunks/ 2>/dev/null
# 應該無輸出！如果有，表示 .env.local 覆蓋了

# 部署
firebase deploy --only hosting
```

## Step 3: Smoke Test

部署完成後執行 smoke test：
```bash
bash smoke-test.sh
```

預期結果：5/5 passed。

如果有失敗，檢查：
1. **CORS** — `curl -sv -H "Origin: https://certimate-titi.web.app" -X OPTIONS <backend-url>`
2. **Cold Start** — Cloud Run `min-instances=0`，首次請求需等待容器啟動
3. **Env Vars** — `gcloud run services describe certimate-titi --region=asia-east1 --format='yaml(spec.template.spec.containers[0].env)'`
4. **Container Logs** — `gcloud run services logs read certimate-titi --region=asia-east1 --limit=20`

---

# 常見問題排查

| 症狀 | 原因 | 修復 |
|------|------|------|
| `Failed to fetch` | 前端 API URL 指向 localhost | 用 env var 覆蓋重新 build |
| `Failed to fetch`（間歇） | Cloud Run cold start | 設定 `--min-instances 1` 或忽略（幾秒後恢復） |
| `name unknown: Repository not found` | Artifact Registry repo 不存在 | `gcloud artifacts repositories create certimate --repository-format=docker --location=asia-east1` |
| `SHORT_SHA` tag 為空 | 非 git trigger 觸發 | 手動傳 `SHORT_SHA=$(git rev-parse --short HEAD)` |
| Container failed to start | 缺少 DATABASE_URL 等 env vars | 用 `--set-env-vars` 或確認已有設定 |
| CORS preflight 失敗 | `ALLOWED_ORIGINS` 未包含前端域名 | 設定 `ALLOWED_ORIGINS=https://certimate-titi.web.app` 或留空（allow all） |

---

# 執行規則

1. **永遠先 smoke test** — 部署後必須跑 `smoke-test.sh` 確認服務正常
2. **驗證 build 產物** — 前端 build 後檢查 `out/` 內沒有 `localhost`
3. **不覆蓋 env vars** — 除非明確要更新，否則 `gcloud run deploy` 不帶 `--set-env-vars`
4. **回報部署結果** — 包含 revision name、service URL、smoke test 結果
