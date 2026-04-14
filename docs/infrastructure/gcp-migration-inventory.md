# GCP 遷移盤點報告

**產出日期**: 2026-04-14
**遷移狀態**: ✅ **已完成**（策略 A，2026-04-14）
**來源帳號**: son731202@gmail.com（保留為 co-owner 備援）
**目標帳號**: certimate.web@gmail.com（已完整接管）
**盤點方式**: `gcloud` CLI 自動掃描

> 本文件為**遷移執行前**的盤點快照。實際遷移採策略 A（原地遷移）：
> Project ID `certimate-titi` 完整保留，所有資源不動，僅 IAM owner + Billing account 改綁。
> GitHub repo 已從 `son1202/certimate` transfer 至 Org `certimate-titi/certimate`。
> Cloud Build trigger 已重建。
> 詳見 `gcp-migration-runbook-strategy-a.md`。

---

## 1. 專案基本資訊

| 項目 | 值 |
|------|-----|
| Project ID | `certimate-titi` |
| Project Number | `63018063271` |
| Display Name | CertiMate TiTi |
| 建立時間 | 2026-03-30 |
| Billing Account | `01A1CB-80419A-E762BE`（啟用中）|

## 2. Cloud Run（2 個服務，asia-east1）

| 名稱 | URL | Image |
|------|-----|-------|
| `certimate` | https://certimate-nfwnajqofa-de.a.run.app | 舊版 commit image |
| `certimate-titi` | https://certimate-titi-nfwnajqofa-de.a.run.app | `:latest`（**目前生產**）|

**注意**：同時有兩個 Cloud Run 服務，可能有一個是遺留的。遷移時只需要重建 `certimate-titi`。

## 3. Cloud SQL

| 項目 | 值 |
|------|-----|
| Instance | `certimate-db` |
| 版本 | **PostgreSQL 18** |
| Region | asia-east1 |
| Tier | `db-f1-micro`（最便宜）|
| 磁碟大小 | 10 GB |
| 公網 IP | 35.221.174.47 |
| 自動備份 | ✅ 啟用 |
| **Databases** | `postgres`（系統）、`certimate`（業務）|

**遷移成本評估**：DB 很小（10 GB 配額，實際資料遠小於此），`pg_dump` + `psql` 遷移預估 **< 5 分鐘**。

## 4. Cloud Storage（3 個 Bucket）

| Bucket | Region | 用途 | 需遷移？ |
|--------|--------|------|:-------:|
| `certimate-titi-data` | asia-east1 | **使用者資源**（PDF / 圖片）**26 MB** | ✅ 必須 |
| `certimate-titi_cloudbuild` | US | Cloud Build 快取 | ❌ 自動重建 |
| `run-sources-certimate-titi-asia-east1` | asia-east1 | Cloud Run 原始碼 | ❌ 自動重建 |

**遷移成本評估**：實際需遷移的資料僅 **26 MB**，`gsutil -m rsync` 30 秒內完成。

## 5. Firebase

| 項目 | 值 |
|------|-----|
| Firebase Project | `certimate-titi`（與 GCP 同 ID）|
| Project Number | 63018063271 |
| Firestore | 尚未確認是否使用（需 Simon 確認）|
| Firebase Auth | 啟用中（前端登入使用）|
| Firebase Hosting | 啟用中（frontend 部署目標）|

## 6. 服務帳號（3 個）

| 帳號 | 用途 | 遷移處理 |
|------|------|---------|
| `63018063271-compute@developer.gserviceaccount.com` | 預設 compute | 新環境自動建立 |
| `firebase-adminsdk-fbsvc@certimate-titi.iam.gserviceaccount.com` | Firebase Admin SDK | **需重新下載金鑰** |
| `github-actions@certimate-titi.iam.gserviceaccount.com` | GitHub Actions CI/CD | **需重建 + 更新 GitHub Secrets** |

## 7. Artifact Registry（3 個 repo）

| Repo | 用途 |
|------|-----|
| `certimate` | Docker 映像檔（手動建立）|
| `cloud-run-source-deploy` | Cloud Run 自動部署 |
| `gcr.io` | 舊版 GCR（向下相容）|

**遷移**：不搬運既有映像檔，新環境重新 build。

## 8. Cloud Build Trigger

| 項目 | 值 |
|------|-----|
| Trigger 名稱 | `rmgpgab-certimate-asia-east1-son1202-certimate--mavfh` |
| GitHub Owner | **son1202**（個人帳號）|
| GitHub Repo | `certimate` |

## 9. GitHub Repo

| 項目 | 值 |
|------|-----|
| 遷移後 remote | `https://github.com/certimate-titi/certimate.git` |
| Owner | **GitHub Org `certimate-titi`**（建於 2026-04-14） |
| 舊路徑 | `https://github.com/son1202/certimate.git`（GitHub 自動 redirect 1 年） |

⚠️ **重要發現**：GitHub repo 也在個人帳號下，不只是 GCP 需要遷移，**GitHub 也要一起**。否則 Cloud Build Trigger 無法連到 repo。

## 10. 其他

| 項目 | 狀態 |
|------|-----|
| Secret Manager | ❌ 未啟用（新環境建立時要同時啟用）|
| BigQuery Dataset | 無（Feature 33 將在新環境建立）|
| 自訂網域 | 無（目前用 `.run.app` 預設網域）|
| DNS | 無需管理 |

---

## 關鍵發現總結

### ✅ 好消息（降低遷移難度）
1. **資料量極小**：DB 配額 10 GB（實際遠小）、Storage 僅 26 MB
2. **無自訂網域**：不必改 DNS
3. **無 Secret Manager**：沒有既有 secrets 需要搬運（目前 secrets 應該都在 .env 或 Cloud Run env vars）
4. **無 BigQuery**：Feature 33 在新環境全新建立即可
5. **Firestore 疑似未使用**（需 Simon 確認）— 減少遷移範圍

### ⚠️ 需要注意
1. **GitHub repo 也要遷移**（或至少要 transfer 給新 GitHub 帳號 / 組織）
2. **Cloud Build Trigger 綁定 son1202 GitHub** — 需重建
3. **兩個 Cloud Run 服務**（`certimate` 與 `certimate-titi`）可能有一個是遺留，建議遷移前先釐清
4. **Cloud Run 目前使用 `:latest` tag 部署**，需確認映像檔 versioning 策略

### 🔴 必須先釐清
1. **GitHub repo 要怎麼處理？**（見下方 Q16）
2. **Firestore 有沒有在用？**
3. **Cloud Run `certimate` 舊服務是否可以刪除？**
