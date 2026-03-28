# CertiMate GCP 部署工作清單

## 建議架構

```
使用者 → Firebase Hosting (前端靜態) → Cloud Run (FastAPI 後端) → Cloud SQL (PostgreSQL)
              ↕                              ↕
        Firebase Auth               Secret Manager
        Firestore                   Cloud Logging
                                    Gemini API
```

## 優先順序

1. **第一階段**（核心）：二 → 三 → 四 → 五 → 六 — 讓系統能跑起來
2. **第二階段**（安全）：一 → 七 → 八 — 安全加固與網域設定
3. **第三階段**（自動化）：九 — CI/CD 自動部署
4. **第四階段**（維運）：十 → 十一 — 監控與上線驗證

---

## 一、GCP 專案與基礎設定

- [ ] **1.1** 建立 GCP 專案（或確認使用現有 Firebase 專案 `gen-lang-client-0751430480`）
- [ ] **1.2** 啟用必要 API：Cloud Run, Cloud SQL, Cloud Build, Artifact Registry, Secret Manager, Cloud Logging
- [ ] **1.3** 設定 Billing Account 並配置預算警報
- [ ] **1.4** 建立服務帳戶（Cloud Run 用、Cloud Build 用），配置最小權限 IAM 角色

## 二、後端容器化

- [ ] **2.1** 撰寫 `backend/Dockerfile`（Python 3.11 + FastAPI + Uvicorn + Gunicorn）
- [ ] **2.2** 建立 `backend/.dockerignore`（排除 tests/、alembic/versions/、\_\_pycache\_\_）
- [ ] **2.3** 本地測試 Docker image 可正常啟動並回應 `/health`
- [ ] **2.4** 在 Artifact Registry 建立 Docker repository

## 三、資料庫（Cloud SQL PostgreSQL）

- [ ] **3.1** 建立 Cloud SQL PostgreSQL 15 實例（選定區域、機器規格、HA 設定）
- [ ] **3.2** 建立 production 資料庫 `certimate-api`
- [ ] **3.3** 建立資料庫使用者（非預設 postgres 帳號）
- [ ] **3.4** 設定自動備份與維護時段
- [ ] **3.5** 執行 Alembic migrations（16 個 migration 檔案套用到 Cloud SQL）
- [ ] **3.6** 驗證 42 張資料表皆已正確建立

## 四、密鑰管理（Secret Manager）

- [ ] **4.1** 建立 Secret：`DATABASE_URL`（Cloud SQL 連線字串）
- [ ] **4.2** 建立 Secret：`JWT_SECRET_KEY`（生成高強度正式密鑰，取代開發用預設值）
- [ ] **4.3** 建立 Secret：`GEMINI_API_KEY`
- [ ] **4.4** 建立 Secret：`FIREBASE_API_KEY`
- [ ] **4.5** 授權 Cloud Run 服務帳戶存取上述 Secrets

## 五、後端部署（Cloud Run）

- [ ] **5.1** 修改 `backend/app/core/config.py` — 支援從環境變數讀取所有設定（已部分支援）
- [ ] **5.2** 修改 `backend/app/main.py` — CORS `allow_origins` 改為限制前端網域（目前是 `*`）
- [ ] **5.3** 修改 `alembic/env.py` — 確認 `DATABASE_URL` 環境變數正確覆寫連線字串
- [ ] **5.4** 設定 Cloud Run 服務：記憶體、CPU、最小/最大實例數、並行數
- [ ] **5.5** 掛載 Secret Manager secrets 為環境變數
- [ ] **5.6** 設定 Cloud SQL 連線（透過 Cloud SQL Auth Proxy / Unix socket）
- [ ] **5.7** 部署並驗證 `/health` 與 `/api/v1/docs` 可存取

## 六、前端部署

- [ ] **6.1** 決定前端部署方式：**維持 Firebase Hosting**（推薦，已有設定）或遷移至 Cloud Storage + Cloud CDN
- [ ] **6.2** 更新 `.env.production`：設定 `APP_URL` 為正式網域
- [ ] **6.3** 設定 `frontend/lib/api/client.ts` 中的 API base URL 指向 Cloud Run 後端
- [ ] **6.4** 建置前端靜態檔案 `npm run build`
- [ ] **6.5** 部署至 Firebase Hosting（`firebase deploy --only hosting`）
- [ ] **6.6** 驗證前端頁面可正常載入，API 呼叫可連通後端

## 七、網路與安全

- [ ] **7.1** 設定 VPC Connector（Cloud Run → Cloud SQL 私有網路通訊）
- [ ] **7.2** Cloud SQL 停用公開 IP（僅允許私有連線）
- [ ] **7.3** 設定 Firestore 安全規則部署（`firebase deploy --only firestore:rules`）
- [ ] **7.4** 後端 CORS 僅允許正式網域
- [ ] **7.5** 確認 JWT_SECRET_KEY 已更換為正式高強度密鑰（≥256 bits）
- [ ] **7.6** 設定 Cloud Armor（選用，DDoS / WAF 防護）

## 八、自訂網域與 SSL

- [ ] **8.1** 購買/設定自訂網域
- [ ] **8.2** Firebase Hosting 綁定自訂網域（前端）
- [ ] **8.3** Cloud Run 設定自訂網域映射（後端 API）
- [ ] **8.4** 驗證 SSL 憑證自動核發完成

## 九、CI/CD Pipeline

- [ ] **9.1** 撰寫 `cloudbuild.yaml`（或 GitHub Actions workflow）
- [ ] **9.2** 後端 pipeline：lint → test（Testcontainers）→ build image → push to Artifact Registry → deploy to Cloud Run
- [ ] **9.3** 前端 pipeline：lint → build → deploy to Firebase Hosting
- [ ] **9.4** 設定 Cloud Build trigger（push to main 觸發）
- [ ] **9.5** 設定 Alembic migration 自動執行策略（Cloud Build step 或 Cloud Run startup job）

## 十、監控與日誌

- [ ] **10.1** 確認 Cloud Run 日誌已自動整合到 Cloud Logging
- [ ] **10.2** 設定 Cloud Monitoring uptime check（`/health` endpoint）
- [ ] **10.3** 設定告警策略：錯誤率、延遲、CPU/Memory 使用率
- [ ] **10.4** 設定 Cloud SQL 監控告警：連線數、儲存空間
- [ ] **10.5** （選用）整合 Error Reporting 追蹤未處理例外

## 十一、正式上線前驗證

- [ ] **11.1** 全功能端到端測試（註冊、登入、上傳、測驗流程）
- [ ] **11.2** 負載測試確認 Cloud Run auto-scaling 正常
- [ ] **11.3** 驗證 Firebase Auth 登入流程在正式網域運作正常
- [ ] **11.4** 驗證 Gemini API 呼叫正常（知識心智圖、AI 考題生成）
- [ ] **11.5** 驗證綠界金流回呼 URL 指向正式環境
- [ ] **11.6** 備份/還原演練（Cloud SQL）

---

> 共 **47 項工作項目**，依四階段優先順序執行。
