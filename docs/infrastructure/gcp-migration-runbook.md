# CertiMate GCP 遷移執行手冊（策略 B — 已凍結未採用）

> ⚠️ **凍結通知**：本手冊為策略 B（新建 project 重建）。
> 實際採用的是**策略 A（原地遷移）**，詳見 `gcp-migration-runbook-strategy-a.md`，並已於 2026-04-14 完成。
> 本檔案僅作為歷史紀錄保留，**不應執行**。

**執行時間**: 2026-04-14 起（未採用）
**來源**: `son731202@gmail.com` / `certimate-titi`
**目標**: `certimate.web@gmail.com` / `<NEW_PROJECT_ID>`（待確認）
**總停機時間預估**: 15-30 分鐘
**對應盤點報告**: `gcp-migration-inventory.md`

---

## 命名與變數（Phase A 前填入）

```bash
# 將這些變數存至 ~/.certimate-migration.env（不進 git）
export OLD_PROJECT="certimate-titi"
export OLD_ACCOUNT="son731202@gmail.com"
export NEW_PROJECT="certimate-titi-prod"   # ← 待 Simon 確認
export NEW_ACCOUNT="certimate.web@gmail.com"
export REGION="asia-east1"
export SQL_INSTANCE="certimate-db"
export DATA_BUCKET="certimate-titi-data"
export NEW_GITHUB_OWNER="<新的 GitHub org 或帳號>"  # ← 待 Simon 確認
export NEW_GITHUB_REPO="certimate"
```

---

## Phase A — 新帳號前置準備（零風險，不動舊環境）

### A1. 登入新 Google 帳號 + 啟用 Billing（Simon 手動）
1. 前往 https://console.cloud.google.com，用 **`certimate.web@gmail.com`** 登入
2. 接受服務條款、啟用 Billing（需綁信用卡；不消費不扣款）
3. 記下新的 Billing Account ID（形如 `XXXXXX-XXXXXX-XXXXXX`）

**檢核**：`Billing → Account management` 看得到新 Billing Account。

### A2. 本地 gcloud 新增新帳號
```bash
gcloud auth login certimate.web@gmail.com
gcloud auth list   # 確認兩個帳號都在
```

### A3. 建立新 Project
```bash
gcloud projects create $NEW_PROJECT \
  --name="CertiMate TiTi Prod" \
  --set-as-default

# 綁定 Billing Account（替換成 A1 記下的 ID）
gcloud billing projects link $NEW_PROJECT \
  --billing-account=XXXXXX-XXXXXX-XXXXXX
```

### A4. 啟用所有必要 API
```bash
gcloud config set project $NEW_PROJECT
gcloud config set account $NEW_ACCOUNT

gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firebase.googleapis.com \
  firebasehosting.googleapis.com \
  identitytoolkit.googleapis.com \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  bigquery.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

### A5. 建立服務帳號（全部走最小權限）
```bash
# 5.1 GitHub Actions CI/CD
gcloud iam service-accounts create github-actions \
  --display-name="github-actions CI/CD"

# 授權（Cloud Run + Artifact Registry + SA Impersonate）
for role in roles/run.admin roles/artifactregistry.writer \
            roles/iam.serviceAccountUser roles/cloudbuild.builds.editor; do
  gcloud projects add-iam-policy-binding $NEW_PROJECT \
    --member="serviceAccount:github-actions@${NEW_PROJECT}.iam.gserviceaccount.com" \
    --role="$role"
done

# 5.2 Cloud Run runtime SA（取代預設 compute SA）
gcloud iam service-accounts create certimate-runtime \
  --display-name="Cloud Run runtime for certimate-titi"

# 授權（讀 secrets、寫 logs、連 Cloud SQL）
for role in roles/secretmanager.secretAccessor roles/logging.logWriter \
            roles/cloudsql.client; do
  gcloud projects add-iam-policy-binding $NEW_PROJECT \
    --member="serviceAccount:certimate-runtime@${NEW_PROJECT}.iam.gserviceaccount.com" \
    --role="$role"
done

# 5.3 Feature 33 BQ reader（Cost Monitor 專用）
gcloud iam service-accounts create cost-monitor-bq-reader \
  --display-name="Feature 33 Cost Monitor BQ Reader"

for role in roles/bigquery.dataViewer roles/bigquery.jobUser; do
  gcloud projects add-iam-policy-binding $NEW_PROJECT \
    --member="serviceAccount:cost-monitor-bq-reader@${NEW_PROJECT}.iam.gserviceaccount.com" \
    --role="$role"
done
```

### A6. 建立 Firebase 專案（綁定剛建立的 GCP 專案）
1. 前往 https://console.firebase.google.com
2. 點 **Add project** → **Add Firebase to a Google Cloud project**
3. 選 `$NEW_PROJECT`
4. 啟用 **Authentication**（同舊環境的 providers：Email/Password、Google、Anonymous）
5. 下載新的 `firebase-adminsdk` 金鑰（Project settings → Service accounts → Generate new private key）
6. 下載 Firebase Config（Project settings → Your apps → Web app）

**檢核**：
- [ ] Authentication tab 顯示 0 個 user（還沒匯入）
- [ ] `firebase-adminsdk-*.json` 已下載至本地 `~/.certimate-migration/`

### A7. 啟用 Firebase Hosting
```bash
# 本機
cd frontend
firebase logout
firebase login   # 用 certimate.web@gmail.com 登入
firebase projects:list   # 應該看到新專案
firebase use --add $NEW_PROJECT --alias default
```

**Phase A 完成條件**：
- [ ] 新 project 可用 `gcloud projects describe` 查到
- [ ] Billing account 已綁定
- [ ] 15 個 API 啟用
- [ ] 3 個服務帳號建立完畢
- [ ] Firebase 專案綁定且 Auth 已啟用
- [ ] Firebase Hosting init 完成

**⏱ 預估時間**: 30-45 分鐘
**🔙 Rollback**: 直接刪除新 project（`gcloud projects delete $NEW_PROJECT`），舊環境零影響。

---

## Phase B — 新環境資源建立（仍不切流量）

### B1. 建立 Cloud SQL instance（新）
```bash
gcloud sql instances create $SQL_INSTANCE \
  --project=$NEW_PROJECT \
  --database-version=POSTGRES_18 \
  --region=$REGION \
  --tier=db-f1-micro \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup \
  --backup-start-time=18:00
```
**等待 ~5 分鐘**（Cloud SQL 啟動慢）

### B2. 建立業務 DB + postgres user 密碼
```bash
gcloud sql databases create certimate \
  --instance=$SQL_INSTANCE \
  --project=$NEW_PROJECT

# 設定 postgres 密碼（存進 ~/.certimate-migration.env）
export NEW_DB_PASSWORD="$(openssl rand -base64 24)"
gcloud sql users set-password postgres \
  --instance=$SQL_INSTANCE \
  --project=$NEW_PROJECT \
  --password="$NEW_DB_PASSWORD"
echo "NEW_DB_PASSWORD=$NEW_DB_PASSWORD" >> ~/.certimate-migration.env
```

### B3. 建立 Cloud Storage bucket
```bash
gcloud storage buckets create gs://${DATA_BUCKET}-new \
  --project=$NEW_PROJECT \
  --location=$REGION \
  --uniform-bucket-level-access
```

### B4. 建立 Artifact Registry
```bash
gcloud artifacts repositories create certimate \
  --project=$NEW_PROJECT \
  --repository-format=docker \
  --location=$REGION \
  --description="CertiMate Docker images"
```

### B5. 建立 BigQuery Dataset（for Feature 33）
```bash
bq --project_id=$NEW_PROJECT mk --dataset \
  --location=asia \
  --description="GCP Billing Export for Feature 33 Cost Monitor" \
  ${NEW_PROJECT}:billing_export
```
**注意**：Billing Export 啟用步驟留到 Phase E（避免舊帳號 billing 寫進新 dataset 造成混淆）。

### B6. 初始化 Secret Manager
```bash
# JWT secret（新產生）
openssl rand -base64 48 | gcloud secrets create jwt-secret-key \
  --data-file=- --project=$NEW_PROJECT

# DB URL（給 Cloud Run 用）
echo -n "postgresql+psycopg://postgres:${NEW_DB_PASSWORD}@/certimate?host=/cloudsql/${NEW_PROJECT}:${REGION}:${SQL_INSTANCE}" | \
  gcloud secrets create database-url \
    --data-file=- --project=$NEW_PROJECT

# AI keys — 全部重新建立（從 .env 讀取或手動填）
for SECRET in anthropic-api-key openai-api-key gemini-api-key voyage-api-key; do
  read -sp "Enter value for $SECRET: " VALUE
  echo
  echo -n "$VALUE" | gcloud secrets create $SECRET \
    --data-file=- --project=$NEW_PROJECT
done

# 授權 Cloud Run runtime SA 讀取
for SECRET in jwt-secret-key database-url anthropic-api-key openai-api-key gemini-api-key voyage-api-key; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:certimate-runtime@${NEW_PROJECT}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$NEW_PROJECT
done
```

**Phase B 完成條件**：
- [ ] Cloud SQL 新 instance `RUNNABLE`
- [ ] 業務 DB `certimate` 建立
- [ ] 新 Storage bucket 建立
- [ ] Artifact Registry `certimate` 建立
- [ ] BigQuery dataset `billing_export` 建立
- [ ] 6 個 secrets 寫入並授權

**⏱ 預估時間**: 30 分鐘
**🔙 Rollback**: 與 Phase A 相同，刪除新 project。

---

## Phase C — 資料同步（仍不切流量）

### C1. 從舊 DB dump（切舊 gcloud 帳號）
```bash
gcloud config set account $OLD_ACCOUNT
gcloud config set project $OLD_PROJECT

# 直接用 Cloud SQL export 到舊 bucket（避開本機網路下載）
gcloud sql export sql $SQL_INSTANCE \
  gs://certimate-titi_cloudbuild/migration/certimate-dump-$(date +%Y%m%d-%H%M).sql \
  --database=certimate
```

### C2. 下載 dump 到本機（避免跨帳號 bucket 權限問題）
```bash
mkdir -p ~/.certimate-migration/dumps
gcloud storage cp gs://certimate-titi_cloudbuild/migration/certimate-dump-*.sql \
  ~/.certimate-migration/dumps/
```

### C3. 匯入新 DB（切新帳號）
```bash
gcloud config set account $NEW_ACCOUNT
gcloud config set project $NEW_PROJECT

# 上傳到新 bucket
gcloud storage cp ~/.certimate-migration/dumps/certimate-dump-*.sql \
  gs://${DATA_BUCKET}-new/migration/

# 授權 Cloud SQL 讀取 bucket
SQL_SA=$(gcloud sql instances describe $SQL_INSTANCE \
  --project=$NEW_PROJECT --format="value(serviceAccountEmailAddress)")
gcloud storage buckets add-iam-policy-binding gs://${DATA_BUCKET}-new \
  --member="serviceAccount:${SQL_SA}" \
  --role="roles/storage.objectViewer"

# Import
gcloud sql import sql $SQL_INSTANCE \
  gs://${DATA_BUCKET}-new/migration/certimate-dump-*.sql \
  --database=certimate --project=$NEW_PROJECT
```

### C4. Storage bucket 資料遷移（26 MB）
```bash
# 跨帳號複製：先 cat credentials 檔 or 簡單用雙 auth
# 從舊帳號下載
gcloud config set account $OLD_ACCOUNT
gcloud storage cp -r gs://certimate-titi-data/\* ~/.certimate-migration/bucket-data/

# 上傳到新帳號
gcloud config set account $NEW_ACCOUNT
gcloud storage cp -r ~/.certimate-migration/bucket-data/\* gs://${DATA_BUCKET}-new/
```

### C5. Firebase Auth 使用者遷移
```bash
# 舊專案 export
gcloud config set account $OLD_ACCOUNT
cd frontend
firebase use certimate-titi
firebase auth:export ~/.certimate-migration/auth-users.json \
  --format=json --project=certimate-titi

# 新專案 import
firebase use $NEW_PROJECT
firebase auth:import ~/.certimate-migration/auth-users.json \
  --project=$NEW_PROJECT --hash-algo=SCRYPT \
  --hash-key=<從舊 Firebase Console 取得 hash config>
```
**注意**：Firebase Auth 匯入需要原本的 hash 參數，可從舊 Firebase Console > Authentication > Users > Import users 說明取得。

### C6. 驗證資料完整性
```bash
# 直接連新 DB 檢查關鍵 table 筆數
gcloud sql connect $SQL_INSTANCE --user=postgres --project=$NEW_PROJECT --database=certimate
```
```sql
-- 檢核查詢（對照舊 DB 的數字）
SELECT 'users' AS table, COUNT(*) FROM users
UNION ALL SELECT 'subjects', COUNT(*) FROM subjects
UNION ALL SELECT 'historical_exams', COUNT(*) FROM historical_exams
UNION ALL SELECT 'questions', COUNT(*) FROM questions
UNION ALL SELECT 'knowledge_nodes', COUNT(*) FROM knowledge_nodes
UNION ALL SELECT 'resources', COUNT(*) FROM resources
UNION ALL SELECT 'resource_chunks', COUNT(*) FROM resource_chunks;
```

**預期數字**（從 CLAUDE.md）：
- `questions` 應該有 **7,992 題**（歷史考古題）
- `historical_exams` 約 **395 個**科目

**Phase C 完成條件**：
- [ ] 新 DB 筆數與舊 DB 100% 一致
- [ ] Storage bucket 檔案數量一致
- [ ] Firebase Auth 使用者數量一致

**⏱ 預估時間**: 20-30 分鐘
**🔙 Rollback**: 清空新 DB 重跑（新環境不影響舊環境）。

---

## Phase D — 切流量（唯一停機時段 15-30 分鐘）

### D0. 宣告停機窗口
- 建議時段：**深夜 02:00-03:00**（CertiMate 使用者最少的時段）
- 前端首頁可加個 banner：「系統將於 04/15 02:00 進行維護，預估 30 分鐘」

### D1. GitHub Repo Transfer（Simon 手動）
1. GitHub.com → `son1202/certimate` → **Settings** → **Transfer ownership**
2. 新 owner 填入新 GitHub 帳號或組織
3. 確認 transfer
4. 本地更新 remote：
   ```bash
   git remote set-url origin https://github.com/${NEW_GITHUB_OWNER}/${NEW_GITHUB_REPO}.git
   git fetch origin
   ```

### D2. 舊環境設為 read-only
```bash
gcloud config set account $OLD_ACCOUNT
gcloud config set project $OLD_PROJECT

# 將舊 Cloud Run instance 縮到 0（阻擋新流量）
gcloud run services update certimate-titi \
  --min-instances=0 --max-instances=0 --region=$REGION
# 此時舊服務會回傳 503
```

### D3. 最後增量同步（針對 Phase C 與 Phase D 之間的新資料）
```bash
# 再跑一次 C1-C3 的 pg_dump + import（差異時間窗約幾小時）
# 這次匯入前先 TRUNCATE 新 DB 的所有 table（避免主鍵衝突）

# 或者更快：直接覆寫新 DB（因為舊環境已停，不會再有新寫入）
```

### D4. 部署新環境的 Backend
```bash
gcloud config set account $NEW_ACCOUNT
gcloud config set project $NEW_PROJECT

cd backend
# 用新專案 build & deploy
gcloud builds submit --region=$REGION \
  --config=cloudbuild.yaml \
  --substitutions=_REGION=$REGION,_PROJECT=$NEW_PROJECT

# 部署 Cloud Run（使用新 runtime SA + Secrets）
gcloud run deploy certimate-titi \
  --image=${REGION}-docker.pkg.dev/${NEW_PROJECT}/certimate/certimate-backend:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=certimate-runtime@${NEW_PROJECT}.iam.gserviceaccount.com \
  --add-cloudsql-instances=${NEW_PROJECT}:${REGION}:${SQL_INSTANCE} \
  --set-secrets="DATABASE_URL=database-url:latest,JWT_SECRET_KEY=jwt-secret-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,GEMINI_API_KEY=gemini-api-key:latest,VOYAGE_API_KEY=voyage-api-key:latest" \
  --allow-unauthenticated
```

### D5. 部署新環境的 Frontend
```bash
cd frontend
# 確認 .env.production 的 NEXT_PUBLIC_API_URL 指向新 Cloud Run URL
# 確認 firebase.ts 的 config 是新 Firebase 專案
npm run build
firebase deploy --only hosting --project=$NEW_PROJECT
```

### D6. Smoke Test（必跑，失敗就 rollback）
```
✅ 新 frontend URL 可開啟
✅ 註冊 / 登入流程正常
✅ 上傳測試 PDF 資源
✅ 知識心智圖生成正常
✅ 出題流程可跑完
✅ 查看錯題地圖
✅ Feature 12a 超級管理員後台可進入
✅ 金流（ECPay）按鈕可觸發（不需真的付款）
```

### D7. 切換流量
**無自訂網域的情況**（目前狀況）：
- 直接把 Firebase Hosting 的新 URL 告訴使用者
- 或將舊 Firebase Hosting 的 `public` 目錄換成一個「已搬家」提示頁 + 新 URL 轉址

**有自訂網域的情況**（未來若加上）：
- 改 DNS A / CNAME 指向新 Firebase Hosting
- TTL 已預設在 300s，5 分鐘生效

**Phase D 完成條件**：
- [ ] Smoke test 全部通過
- [ ] 使用者能正常存取新環境
- [ ] 舊環境返回 503

**⏱ 預估停機時間**: **15-30 分鐘**
**🔙 Rollback**:
- D2 發現問題：`gcloud run services update certimate-titi --min-instances=1 --max-instances=10`（恢復舊環境）
- D6 失敗：同上，立即恢復舊環境，新環境保留待排查

---

## Phase E — 收尾（7 天穩定期後）

### E1. 新環境穩定後（Day 1-7）
- 持續監控 Cloud Run logs、錯誤率
- 使用者回報即時處理
- 舊環境 **完整保留但 min-instances=0**（不接流量但保留資料）

### E2. 啟用 Feature 33 的 Billing Export（Day 1）
依 `gcp-billing-export-setup.md` 第 1-3 節執行，但把所有 project id 改為 `$NEW_PROJECT`。

### E3. Day 7 清理
```bash
# 確認新環境穩定、無 rollback 需求後
gcloud config set account $OLD_ACCOUNT
gcloud config set project $OLD_PROJECT

# 停舊 Cloud Run
gcloud run services delete certimate-titi --region=$REGION
gcloud run services delete certimate --region=$REGION

# 停舊 Cloud SQL（先 backup）
gcloud sql backups create --instance=$SQL_INSTANCE
gcloud sql instances delete $SQL_INSTANCE

# 清空並刪除舊 bucket
gcloud storage rm -r gs://certimate-titi-data/\*
gcloud storage buckets delete gs://certimate-titi-data

# 停 Billing
gcloud billing projects unlink $OLD_PROJECT

# 最後：關閉整個舊 project（30 天後永久刪除）
gcloud projects delete $OLD_PROJECT
```

### E4. 更新文件
- `CLAUDE.md`：專案 ID、URL
- `backend/CLAUDE.md`：deployment 相關
- `frontend/.env.example`：Firebase config 範例
- `README.md`：clone 指令、部署指令

### E5. 啟動 Feature 33 Layer 3 實作
遷移完成後，回到 titi-commander，繼續 Feature 33 Layer 3（後端工程師單人任務）。

**Phase E 完成條件**：
- [ ] 舊環境完全關閉
- [ ] 舊 Billing 已解綁
- [ ] 文件全部更新
- [ ] Feature 33 Layer 3 啟動

**⏱ 分散在 7-14 天**
**🔙 Rollback**: Day 7 前皆可重新啟動舊環境；Day 30 後舊 project 永久刪除，不可逆。

---

## 高階風險與對策總表

| 風險 | 發生階段 | 對策 |
|------|:--------:|------|
| 新 Billing Account 綁卡失敗 | A | 先確認信用卡有效；失敗時不影響舊環境 |
| Cloud SQL 版本不一致 | B | 明確指定 POSTGRES_18，與舊環境一致 |
| DB 匯入主鍵衝突 | C | 先 TRUNCATE 再 import；或用 `--clean` flag |
| Firebase Auth hash 參數不符 | C | 從 Firebase Console > Authentication > Users > Import 頁面取 hash config |
| GitHub transfer 後 Cloud Build 失效 | D | Phase D 重建 trigger 時用新 GitHub remote |
| Smoke test 失敗 | D | 立即 rollback 舊環境；新環境保留除錯 |
| 使用者反映資料缺失 | D/E | 檢查 Phase C 的筆數比對；必要時補增量匯入 |
| 舊 Billing 意外扣款 | E | Phase E 明確 unlink billing；設 budget alert |

---

## 執行時程建議

| 階段 | 建議時段 | 預估 |
|------|---------|------|
| Phase A | 任何時段 | 30-45 分鐘 |
| Phase B | 任何時段（接 Phase A 或隔日）| 30 分鐘 |
| Phase C | 流量低時段（避免增量同步時差太大）| 20-30 分鐘 |
| Phase D | **深夜 02:00-03:00** | **15-30 分鐘停機** |
| Phase E | 分散 7-14 天 | 非連續 |

**全部完成總工期**：1-2 個工作日集中執行 + 7 天穩定觀察期
