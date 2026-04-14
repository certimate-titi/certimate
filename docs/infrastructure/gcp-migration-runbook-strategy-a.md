# CertiMate GCP 遷移執行手冊 — 策略 A（原地遷移）

**狀態**: ✅ **已完成於 2026-04-14**（Phase Pre-A → D' 全部完成）
**策略**: Transfer Billing + IAM Ownership（**不建新 project**）
**來源帳號**: son731202@gmail.com（保留為 co-owner 備援）
**目標帳號**: certimate.web@gmail.com（已完整接管）
**保留**: Project ID `certimate-titi` / 所有資源 / URL / 使用者資料
**總停機時間**: **零**
**實際工期**: 約 4 小時集中執行（含 GitHub Org transfer 與 Cloud Build trigger 重建）

> **附帶完成項目**：
> - GitHub repo 從 `son1202/certimate` transfer 至 `certimate-titi/certimate` Org
> - Cloud Build trigger 重建為 `Build-and-deploy-to-Cloud-Run-service-certimate-on-push-to-main`
> - GCP Native Budget 護欄：1500 TWD/月，三級告警 → son731202 + certimate.web 雙 email
> - Cloud Monitoring notification channels 已驗證可寄信
> - Phase E' 觀察期：無時間壓力，son731202 永久保留為備援 co-owner

---

## 關鍵前提

以下資源**完全不動**：
- ✅ Cloud SQL `certimate-db` 與所有資料
- ✅ Cloud Storage `certimate-titi-data`
- ✅ Cloud Run `certimate-titi` 服務與 URL
- ✅ Firebase Auth 使用者
- ✅ Artifact Registry 的既有 Docker 映像檔
- ✅ 所有 Secret Manager（目前為空，之後建立時直接進 certimate-titi）

**只變動**：
- 🔄 Billing Account（付款人）
- 🔄 IAM Owner（擁有者）
- 🔄 GitHub repo owner（獨立於 GCP）

---

## Phase A' — 新帳號接手準備（10 分鐘，Simon 手動）

### A'1. 新帳號啟用 GCP + Billing（Simon 瀏覽器操作）
1. 登出瀏覽器的 son731202 帳號
2. 用 `certimate.web@gmail.com` 登入 https://console.cloud.google.com
3. 接受 GCP 服務條款
4. 前往 **Billing** → **Create account** → 建立新的 Billing Account
5. 綁定信用卡（**不消費不扣款**）
6. 記下新 Billing Account ID（格式：`XXXXXX-XXXXXX-XXXXXX`）

### A'2. 本地 gcloud 新增新帳號
```bash
gcloud auth login certimate.web@gmail.com
# 瀏覽器開啟 → 授權 → 回來
gcloud auth list  # 應該看到兩個 ACCOUNT
```

**A' 完成條件**：
- [ ] 新 Billing Account 已建立
- [ ] gcloud 已認證新帳號
- [ ] 記下 `NEW_BILLING_ACCOUNT=XXXXXX-XXXXXX-XXXXXX`

---

## Phase B' — IAM 交接（15 分鐘，含雙帳號操作）

### B'1. 舊帳號授權新帳號為 Owner
```bash
gcloud config set account son731202@gmail.com
gcloud config set project certimate-titi

gcloud projects add-iam-policy-binding certimate-titi \
  --member="user:certimate.web@gmail.com" \
  --role="roles/owner"
```
此時 certimate.web 會收到一封通知 email，但不需要特別確認，權限立即生效。

### B'2. 驗證新帳號可存取
```bash
gcloud config set account certimate.web@gmail.com
gcloud config set project certimate-titi

# 逐項驗證能看到所有資源
gcloud projects describe certimate-titi
gcloud run services list --region=asia-east1
gcloud sql instances list
gcloud storage buckets list
gcloud artifacts repositories list --location=asia-east1
gcloud iam service-accounts list
```
**預期**：全部指令都能成功列出資源。

**B' 完成條件**：
- [ ] 新帳號為 `certimate-titi` 的 Owner
- [ ] 新帳號 gcloud 能看到所有資源

---

## Phase C' — Billing 切換（10 分鐘）

### C'1. 把 project 改綁新 Billing Account
```bash
# 仍用新帳號（需對兩個 billing account 都有權限）
gcloud config set account certimate.web@gmail.com

# 注意：新帳號需要同時對新 billing account 有 Billing Account User 權限
#       以及對 certimate-titi 有 Project Billing Manager 權限（已含在 owner 裡）
gcloud billing projects link certimate-titi \
  --billing-account=<NEW_BILLING_ACCOUNT_ID>
```

### C'2. 驗證切換成功
```bash
gcloud billing projects describe certimate-titi
# 應該顯示 billingAccountName: billingAccounts/<NEW>
```

### C'3. 確認舊 Billing 已停止累計
- 前往 GCP Console → Billing → 舊 Billing Account → Reports
- 隔天確認 `certimate-titi` 不再累計新費用

**C' 完成條件**：
- [ ] `gcloud billing projects describe` 顯示新 billing account
- [ ] 舊 billing account 的 reports 不再累計 certimate-titi 費用

**⚠️ 關鍵風險**：改綁 billing 後舊帳號仍會收到本月截至切換前的帳單（例如 4/1-4/14 費用）。這是正常的，不是故障。

---

## Phase D' — GitHub Repo Transfer（15 分鐘，獨立於 GCP）

### D'1. 決定新 GitHub owner（待 Simon 確認）
- 選項 A：新建個人帳號 `certimate-web`
- 選項 B：新建 Organization `CertiMate`（建議，利於團隊協作）
- 選項 C：先不遷，維持 `son1202/certimate`（不建議，與本次遷移動機衝突）

### D'2. GitHub 網頁操作
1. 前往 https://github.com/son1202/certimate/settings
2. 捲到最下方 **Danger Zone** → **Transfer ownership**
3. 輸入新 owner 名稱 + repo 名確認
4. 新 owner 需登入 GitHub 接受 transfer

### D'3. 本機更新 remote
```bash
cd /Users/simon/certimate/project
git remote set-url origin https://github.com/<NEW_OWNER>/certimate.git
git fetch origin
git pull --rebase
```

### D'4. 重建 Cloud Build Trigger
既有 trigger `rmgpgab-certimate-asia-east1-son1202-certimate--mavfh` 連的是舊 GitHub owner。

```bash
gcloud config set account certimate.web@gmail.com
gcloud config set project certimate-titi

# 刪舊 trigger
gcloud builds triggers delete \
  rmgpgab-certimate-asia-east1-son1202-certimate--mavfh \
  --region=asia-east1

# 重建：GCP Console 上連接新 GitHub
# 前往 https://console.cloud.google.com/cloud-build/triggers?project=certimate-titi
# → Connect Repository → 授權新 GitHub → 選 <NEW_OWNER>/certimate
# → Create Trigger（push to master → cloudbuild.yaml）
```

### D'5. 驗證 CI/CD
```bash
# 推一個 no-op commit 觸發 build
git commit --allow-empty -m "chore: verify cloud build after gcp migration"
git push origin master
# 在 Cloud Build Console 確認 build 啟動
```

**D' 完成條件**：
- [ ] Repo 已在新 GitHub owner 底下
- [ ] 本機 remote URL 已更新
- [ ] Cloud Build Trigger 重建且觸發成功

---

## Phase E' — 穩定期 + 舊帳號權限清理（7-14 天）

### E'1. Day 1-7 觀察
- 留著 son731202 為 `certimate-titi` 的 Owner 作為雙保險
- 每天檢查：
  - Cloud Run 正常運作
  - Billing 產生新費用在新 billing account
  - CI/CD 可正常 deploy

### E'2. Day 7：降級舊帳號
確認新帳號完全接手後，將 son731202 的 owner 降為 editor（再觀察 3 天），最後移除：

```bash
# Day 7：降為 editor
gcloud config set account certimate.web@gmail.com

gcloud projects remove-iam-policy-binding certimate-titi \
  --member="user:son731202@gmail.com" \
  --role="roles/owner"

gcloud projects add-iam-policy-binding certimate-titi \
  --member="user:son731202@gmail.com" \
  --role="roles/editor"
```

```bash
# Day 14：完全移除
gcloud projects remove-iam-policy-binding certimate-titi \
  --member="user:son731202@gmail.com" \
  --role="roles/editor"
```

### E'3. Service Account 金鑰輪替（建議，非強制）
既有 `github-actions` 與 `firebase-adminsdk` service account 的金鑰在 son731202 當 owner 時建立。可選擇性輪替：

```bash
# 為 github-actions SA 產生新金鑰
gcloud iam service-accounts keys create ~/new-github-actions-key.json \
  --iam-account=github-actions@certimate-titi.iam.gserviceaccount.com

# 更新 GitHub Secrets 裡的 GCP_SA_KEY
# 然後刪除舊金鑰
gcloud iam service-accounts keys list \
  --iam-account=github-actions@certimate-titi.iam.gserviceaccount.com
gcloud iam service-accounts keys delete <OLD_KEY_ID> \
  --iam-account=github-actions@certimate-titi.iam.gserviceaccount.com
```

### E'4. 啟動 Feature 33 Layer 3
GCP 遷移收尾後，回到 titi-commander，繼續 Feature 33 Layer 3 的後端實作（在同一個 `certimate-titi` 專案，BQ Billing Export 在新 billing account 上啟用即可）。

### E'5. 更新文件
- `docs/infrastructure/gcp-migration-inventory.md` 加註「已遷移，新擁有者 certimate.web」
- 凍結 `gcp-migration-runbook.md`（策略 B 版），標註「未採用」

**E' 完成條件**：
- [ ] 7-14 天觀察無事
- [ ] son731202 權限完全移除
- [ ] 文件更新
- [ ] Feature 33 Layer 3 啟動

---

## 風險與 Rollback 總表

| 風險 | 發生階段 | Rollback |
|------|:--------:|---------|
| 新 Billing 綁卡失敗 | A' | 不影響既有 project，重試即可 |
| 新帳號 IAM 授權錯誤 | B' | 舊帳號仍是 owner，可隨時移除新帳號權限 |
| Billing 改綁失敗 | C' | 重新綁回舊 billing account |
| GitHub transfer 中途 | D' | Transfer 需雙方同意，未完成前不會影響 repo |
| Cloud Build Trigger 失效 | D' | 舊 trigger 刪除前先建新的 |
| 舊帳號被停用但新帳號尚未接手 | 全程 | **關鍵**：必須先確認 B' 完成才能讓 son731202 停用 |

---

## 關鍵安全守則

🔴 **Son731202 停用的時間點**必須在 Phase E' 完成之後。否則：
- 若 Phase B' 之後、E' 之前 son731202 被停用，project 仍然屬於 certimate.web（安全）
- 但若 Phase B' 之前 son731202 停用，整個 project 會失去唯一 Owner，**極度危險**

**建議時序**：
1. 先完成 Phase A'、B'（讓 certimate.web 成為 Owner）
2. 再處理 son731202 的停用流程（如果有時間壓力）
3. 最後才是 Phase C'、D'、E'

---

## 執行順序建議

| 階段 | 建議時間 | 是否可中斷 |
|:----:|---------|:---------:|
| A' | 現在 | ✅ 可中斷 |
| B' | 接 A' | ✅ 可中斷（舊帳號權限還在）|
| C' | 接 B' | ✅ 可中斷 |
| D' | 可延後（獨立任務）| ✅ 可中斷 |
| E' | 7-14 天 | - |

**最小可行執行**：只跑 A' + B'（15-25 分鐘）就能達成「certimate.web 可完整操作 project」的狀態，足以應付 son731202 即將停用的急迫性。C'/D'/E' 可分批進行。
