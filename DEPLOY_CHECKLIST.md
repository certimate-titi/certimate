# CertiMate GCP 部署檢查清單 ✅

**準備狀態**：✅ 程式碼已準備就緒，可以部署

---

## 在本機部署（必須在本機執行）

### 前置條件
```bash
# 1. 安裝 Google Cloud SDK
curl https://sdk.cloud.google.com | bash

# 2. 安裝 Firebase CLI
npm install -g firebase-tools

# 3. 驗證工具
gcloud --version
firebase --version
```

### 執行部署

```bash
cd /home/user/certimate

# 登入 GCP
gcloud auth login
gcloud config set project certimate-titi

# 選項 A：完整部署（後端 + 前端）
./deploy.sh all

# 選項 B：只部署後端
./deploy.sh backend

# 選項 C：只部署前端
./deploy.sh frontend

# 選項 D：只執行基礎設施設置
./deploy.sh infra
```

---

## 預期部署時間

| 步驟 | 時間 | 說明 |
|------|------|------|
| Cloud Build | 5-10 分鐘 | Build Docker image + push to Artifact Registry |
| Cloud Run Deploy | 2-3 分鐘 | Deploy revised service |
| Frontend Build | 3-5 分鐘 | Next.js build + static export |
| Firebase Deploy | 1-2 分鐘 | Upload to hosting |
| Smoke Test | 1-2 分鐘 | Verify all endpoints |
| **總計** | **15-25 分鐘** | 完整部署 |

---

## 環境變數已配置

✅ **後端環境變數**（已在 `gcloud run deploy` 中設置）

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

✅ **前端環境變數**（Build 時設置）

```
NEXT_PUBLIC_API_URL=https://certimate-titi-63018063271.asia-east1.run.app/api/v1
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyA5LshjGNrYxSOabPqaxB_EQb-AMjd-6ks
```

---

## 部署成功標誌

部署完成後，應看到：

```
✓ Deployment Successful!
Backend:  https://certimate-titi-63018063271.asia-east1.run.app
Frontend: https://certimate-titi.web.app

Demo account:
  Email:    admin@certimate.com
  Password: admin123

Result: 8/8 passed ✅ (Smoke Test)
```

---

## 驗證部署

### 1. 檢查後端健康狀態

```bash
curl https://certimate-titi-63018063271.asia-east1.run.app/health
# 預期：{"status": "ok"}
```

### 2. 檢查 API 文件

```
https://certimate-titi-63018063271.asia-east1.run.app/api/v1/docs
```

### 3. 測試登入（Demo 帳號）

```bash
curl -X POST https://certimate-titi-63018063271.asia-east1.run.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@certimate.com","password":"admin123"}'

# 預期：{"access_token": "...", "token_type": "bearer", ...}
```

### 4. 存取前端

```
https://certimate-titi.web.app
```

---

## 常見部署問題與解決

| 問題 | 原因 | 解決方案 |
|------|------|---------|
| `gcloud: command not found` | Cloud SDK 未安裝 | 安裝 Google Cloud SDK |
| `Authentication required` | 未登入 GCP | 執行 `gcloud auth login` |
| `Permission denied` | IAM 權限不足 | 確保帳號是 Project Owner |
| `Image not found` | Artifact Registry repo 不存在 | 執行 `./deploy.sh infra` |
| `Database connection failed` | DATABASE_URL 不正確 | 檢查 Cloud SQL instance 名稱 |
| `Frontend still pointing to localhost` | .env.local 未被覆蓋 | 刪除 `frontend/.env.local` 後重新 build |
| `Smoke test failed — 502 Bad Gateway` | Cold start（min-instances=0） | 容器啟動後 1-2 秒恢復，無需修復 |

---

## 監控部署進度

### 查看 Cloud Run 部署日誌

```bash
# 查看最新 50 行日誌
gcloud run services logs read certimate-titi --region=asia-east1 --limit=50

# 即時監控（follow mode）
gcloud run services logs read certimate-titi --region=asia-east1 --follow
```

### 查看 Cloud Build 日誌

```bash
gcloud builds list --limit=5
gcloud builds log <BUILD_ID>
```

### 查看 Firebase 部署日誌

```bash
firebase hosting:channel:list
firebase deploy --only hosting
```

---

## 回滾到上個版本

如果部署有問題，快速回滾：

```bash
# 查看部署歷史
gcloud run revisions list --service certimate-titi --region=asia-east1 --limit=5

# 回滾到上個版本
PREVIOUS_REVISION=$(gcloud run revisions list --service certimate-titi --region=asia-east1 \
  --format='value(name)' --limit=2 | tail -1)

gcloud run services update-traffic certimate-titi \
  --to-revisions $PREVIOUS_REVISION=100 \
  --region=asia-east1
```

---

## 部署後檢查項目

- [ ] 後端服務在 Cloud Run 中執行
- [ ] 前端靜態內容在 Firebase Hosting 上線
- [ ] Demo 帳號可正常登入
- [ ] 所有 8 個 smoke test 通過 ✅
- [ ] 資料庫連線正常（無 502 錯誤）
- [ ] 前端 API 呼叫指向正確 URL（非 localhost）
- [ ] CORS 允許前端域名

---

## 支持與進一步步驟

1. **監控成本**：https://console.cloud.google.com/billing
2. **設置告警**：https://console.cloud.google.com/monitoring
3. **查看日誌**：https://console.cloud.google.com/logs
4. **設置自動部署**：使用 GitHub Actions + Cloud Build

---

## 快速參考

| 服務 | URL |
|------|-----|
| **Backend API** | https://certimate-titi-63018063271.asia-east1.run.app |
| **Frontend** | https://certimate-titi.web.app |
| **API Docs** | https://certimate-titi-63018063271.asia-east1.run.app/api/v1/docs |
| **GCP Console** | https://console.cloud.google.com/run?project=certimate-titi |
| **Firebase Console** | https://console.firebase.google.com/project/certimate-titi |
