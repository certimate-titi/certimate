# CLAUDE.md

本文件為 Claude Code (claude.ai/code) 在此專案中的開發指引。

## 專案概述

CertiMate 是一個 AI 驅動的證照考試備考 SaaS 平台，前端使用 Next.js，後端使用 Python (FastAPI)，以 BDD E2E 測試驅動開發。

## 專案結構

- `frontend/` — Next.js 前端應用 (UI)
- `backend/` — FastAPI 後端 (API + BDD E2E 測試)
- `project/` — 商業規劃文件、市場分析與 BDD `.feature` 規格
  - `project/specs/entity/erm.dbml` — 資料庫結構的**唯一真實來源 (SSOT)**（DBML 格式，43+ 張表）
  - `project/features/` — 定義產品需求的 Gherkin `.feature` 檔案

## 開發指令

### 前端（於 `frontend/` 目錄下）

```bash
cd frontend
npm install          # 安裝依賴
npm run dev          # 啟動開發伺服器（使用 .next-dev/ 建置）
npm run build        # 正式環境建置（靜態匯出至 .next/）
npm run lint         # ESLint 檢查
npm run clean        # 清除 Next.js 快取
```

環境變數：將 `.env.example` 複製為 `.env.local`，填入 `GEMINI_API_KEY`、`APP_URL`、`NEXT_PUBLIC_FIREBASE_API_KEY`。

### 後端（於 `backend/` 目錄下）

```bash
cd backend
.venv/bin/python -m behave tests/features/          # 執行所有 BDD E2E 測試
.venv/bin/python -m behave tests/features/ --tags=~@ignore  # 僅執行已完成的 features
.venv/bin/python -m behave tests/features/01-身分驗證.feature  # 執行特定 feature
.venv/bin/python -m uvicorn app.main:app --reload   # 啟動開發用 API 伺服器
```

**重要**：必須使用 `.venv/bin/python`（Python 3.13），系統 `python3` 是 3.9 不相容。

需要 Docker 來執行 Testcontainers (PostgreSQL)。測試不需要 `.env` — Testcontainers 會自動啟動 PostgreSQL 容器。

## 架構

### 技術棧 — 前端
- **框架**: Next.js 15 (App Router) + React 19 + TypeScript (strict mode)
- **樣式**: TailwindCSS 4 + PostCSS
- **認證/資料庫**: Firebase Auth + Firestore
- **AI**: Google Gemini API (`@google/genai`)
- **部署**: Firebase Hosting（靜態匯出，`output: 'export'`）
- **動畫**: Motion library
- **圖表**: Recharts

### 技術棧 — 後端
- **框架**: FastAPI + Uvicorn
- **ORM/資料庫**: SQLAlchemy 2.0 + PostgreSQL (psycopg 3) + Alembic migrations
- **BDD 測試**: Behave + Testcontainers (PostgreSQL) + FastAPI TestClient
- **認證**: PyJWT (HS256)

### 路徑別名
`@/*` 對應 `frontend/` 根目錄（例如 `@/lib/api/services`、`@/types`）。

### 重要目錄 — 前端（`frontend/` 下）

| 路徑 | 說明 |
|------|------|
| `app/` | Next.js App Router 頁面 — 公開頁、認證、考試流程、儀表板、管理後台 |
| `components/` | 可重用 React 元件（導覽列、遊戲化、引導步驟） |
| `lib/api/services.ts` | **API 服務層** — 所有資料操作都經由此處。目前回傳 mock 資料；函式簽名即為未來後端整合的 API 合約 |
| `lib/api/client.ts` | HTTP 客戶端設定 |
| `lib/auth-context.tsx` | 認證狀態管理（Firebase Auth + localStorage demo 模式） |
| `lib/onboarding-context.tsx` | 引導流程狀態 |
| `types/models.ts` | 領域模型（User、Document、Exam、Question 等） |
| `types/api.ts` | API 請求/回應型別定義 |
| `hooks/` | 自訂 React hooks |
| `firebase.ts` | Firebase 初始化 + 管理員稽核日誌 |
| `firestore.rules` | Firestore 安全規則 |

### 重要目錄 — 後端（`backend/` 下）

| 路徑 | 說明 |
|------|------|
| `app/main.py` | FastAPI 應用程式進入點（31 個 router） |
| `app/core/config.py` | 設定、路徑、JWT 組態 |
| `app/core/deps.py` | 依賴注入（DB session、JWT 認證、多租戶 RLS） |
| `app/core/security.py` | SSRF 防護、URL 白名單 |
| `app/models/` | 40 個 SQLAlchemy ORM 模型（衍生自 `erm.dbml`） |
| `app/repositories/` | 15 個 Repository 類別（SQLAlchemy 資料庫存取） |
| `app/services/` | 48 個業務邏輯服務 |
| `app/api/` | 31 個 FastAPI 路由（API endpoints） |
| `app/schemas/` | Pydantic 請求/回應 schemas |
| `app/scripts/` | CLI 工具（考古題匯入、租戶清除、Prompt seed） |
| `scripts/crawlers/` | 高普考爬蟲工具（moex_simple, auto_catalog_generator） |
| `data/historical_questions/` | 爬蟲產出 JSON（7,992 題） + PDF |
| `alembic/` | 資料庫遷移（001-040） |
| `tests/features/` | 43 個 Behave BDD feature 檔案 + step definitions |
| `tests/features/environment.py` | Testcontainers 生命週期（PostgreSQL + context 初始化） |
| `tests/features/helpers/` | JWT helper、測試工具 |
| `tests/features/steps/` | 37 個子領域 step definitions |
| `tests/features/steps/common_then/` | 共用 Then 步驟（操作成功/失敗/錯誤訊息） |

### 後端 Step Definition 組織

Step definitions 遵循事件風暴分類：
```
tests/features/steps/{subdomain}/
  ├── aggregate_given/   # 資料庫實體建立（Given 步驟）
  ├── commands/          # HTTP API 呼叫（When 步驟）
  ├── aggregate_then/    # 資料庫狀態驗證（Then 步驟）
  └── readmodel_then/    # API 回應驗證（Then 步驟）
```

每個 step 獨立一個檔案（一檔一 step 模式）。所有 step 模組必須在 `tests/features/steps/__init__.py` 中明確 import。

目前的子領域（37 個）：`account_settings`、`admin`、`admin_finance`、`admin_moderation`、`admin_settings`、`ai_gen`、`anomaly`、`auth`、`b2b`、`community`、`confidence_calibration`、`dashboard`、`difficulty_progression`、`ecpay`、`edu_plan`、`exam`、`exam_result`、`feedback`、`fup`、`knowledge_map`、`knowledge_merge`、`mock_exam`、`onboarding`、`pomodoro`、`pricing`、`prompt_template`、`question_retirement`、`resource`、`resource_lib`、`reverse_engineering`、`schedule`、`subscription`、`subscription_trial`、`subscription_upgrade`、`tenant_security`、`wrong_answer`、`wrong_answer_map`。共用步驟放在 `common_then/`。

### 頁面結構
- **公開頁面**: 首頁 (`/`)、登入、註冊、忘記密碼
- **已認證頁面**: 儀表板、引導流程、帳戶設定
- **考試流程**: exam/setup -> exam/workspace -> exam/results
- **功能頁面**: 知識心智圖、錯題複習
- **管理後台**: 機構管理 (B2B)、平台管理（稽核日誌、使用者管理、財務、審核、系統設定）

### 領域概念
- **訂閱方案**: FREE、PRO_199、PRO_PLUS_399、ULTRA_1599
- **文件來源**: PDF、Markdown、YouTube URL、手寫圖片
- **測驗類型**: 模擬機考、間隔複習、閃卡集
- **遊戲化**: 連續學習天數、成就、每日任務、成長里程碑

### 重要模式 — 前端
- 所有頁面皆為客戶端渲染 (`'use client'`) — 應用程式為靜態匯出
- Auth context 同時支援 Firebase Auth 與 localStorage demo 模式
- `lib/api/services.ts` 中的服務層是所有 API 呼叫的唯一真實來源 — 實作後端整合時，修改此處的實作但不更改函式簽名
- 可透過 `DISABLE_HMR=true` 環境變數停用 HMR（用於 AI Studio）
- 建置時忽略 ESLint 錯誤（`next.config.ts` 中的 `ignoreDuringBuilds: true`）

### 重要模式 — 後端
- **DBML 是資料庫結構的唯一真實來源**（`project/specs/entity/erm.dbml`）。所有 SQLAlchemy 模型必須與 DBML 定義一致。
- **TDD 流程**: Schema Analysis -> Step Template -> Red（測試以 HTTP 404 失敗）-> Green（實作 API）-> Refactor
- **E2E 測試使用 Testcontainers** — 每次測試 session 啟動真實 PostgreSQL 容器，套用 Alembic migrations，每個 scenario 之間清除資料表
- **context** 用於在 Given/When/Then 步驟間傳遞狀態：`context.db_session`、`context.api_client`、`context.jwt_helper`、`context.ids`、`context.memo`、`context.last_response`
- **API 前綴**: `/api/v1` — 所有端點都在此前綴下
- **JSON 欄位命名**: 所有 API 請求/回應欄位使用 snake_case
- **紅燈階段不實作後端 API** — 測試應以 HTTP 404 失敗；API 端點僅在綠燈階段新增
- **Alembic migrations** 位於 `backend/alembic/versions/`，使用遞增編號（001–040）。建立新 migration 時使用 `--rev-id` 指定下一個編號（下一個 = 041）

## 功能規格

43 個 BDD `.feature` 檔案定義產品需求，涵蓋：

| # | 功能 | 說明 |
|---|------|------|
| 01 | 身分驗證 | 註冊、登入、Email 驗證、角色管理、EDU 邀請 |
| 02 | 資源上傳 | PDF、Markdown、YouTube、手寫圖片上傳、SSRF 防護 |
| 03/03a/03b | 知識心智圖 | 心智圖生成 + 導航 + AI 教練 |
| 04/04a | 測驗設定 | 考試設定 + AI 四階段考題生成 Pipeline |
| 05 | 模擬機考 | 模擬考試情境、KaTeX 公式支援 |
| 06 | 測驗結果 | 考試結果與分析 |
| 07 | 錯題複習與AI教練 | 錯題複習 + AI 教練指導 + 配額管理 |
| 08/08a/08b | 訂閱管理 | 訂閱方案 + 綠界金流 + 付款後權限更新 + EDU 衝突處理 |
| 09 | 學習記憶排程 | 艾賓浩斯遺忘曲線排程 |
| 10 | B2B機構管理後台 | 教育機構管理控制台 |
| 11 | 資源庫管理 | 共享資源庫管理 |
| 12/12a/12b/12c | 平台管理後台 | 平台管理（財務、審核、系統設定） |
| 13 | 個人儀表板與成就系統 | 儀表板與成就系統 |
| 14 | 社群歸屬與主動關懷 | 社群互動與主動關懷 |
| 15 | 首次登入引導 | 引導流程與學習歷程建立 |
| 16 | 異常維修管理 | 異常追蹤與維修排程管理 |
| 17 | 意見反饋 | 使用者意見回饋收集 |
| 18 | 題目分類與考試趨勢 | Bloom 認知層次分類 + 趨勢分析 |
| 18(定價) | 定價與升級引導 | 付費牆 + 升級流程 |
| 19 | 交錯練習 | 混合科目練習模式 |
| 20 | 信心度校準 | 作答信心度標註與校準 |
| 21 | 番茄鐘學習節奏 | 時間管理 + 專注模式 |
| 22 | 帳號設定與個人偏好 | 個人資料 + 學習偏好 |
| 23 | 考古題題庫管理 | 歷史考題匯入 + 信度標示 |
| 24 | 系統公告管理 | 平台通知與公告 |
| 25 | AI考題退場與放榜 | 題目過期管理 + 成績發布 |
| 26 | 考綱逆向工程 | 考試大綱分析與知識點對應 |
| 27 | 個人化錯題地圖 | 弱點可視化 + AI 建議 |
| 28 | 階層式難度遞進 | 漸進式難度調整 |
| 29 | 知識樹合併對齊 | 多資源知識節點合併 |
| 30 | Prompt模板管理 | 版本控制 + A/B 測試 |
| 31 | 多租戶安全與資料隔離 | RLS + SSRF + 租戶資料清除 |

Feature 檔案存放於 `project/features/`（規格）與 `backend/tests/features/`（測試執行）。

## BDD E2E 測試流程

後端對每個 `.feature` 檔案遵循自動化 BDD E2E 流程：

1. **Schema Analysis** — 驗證 feature 與 DBML 一致性，建立/更新 ORM 模型
2. **Step Template** — 生成 behave step definition 骨架（含 TODO 註解）
3. **Red（紅燈）** — 實作完整 step definitions + repositories（測試失敗：HTTP 404）
4. **Green（綠燈）** — 實作 FastAPI endpoints + services（測試通過）
5. **Refactor（重構）** — 在測試保護下改善程式碼品質

Feature 檔案複製至 `backend/tests/features/` 執行。紅燈階段完成後移除 `@ignore` 標籤。
