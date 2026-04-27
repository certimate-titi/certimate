# CLAUDE.md

本文件為 Claude Code 在 CertiMate (TiTi) 專案中的開發指引。子目錄另有 [backend/CLAUDE.md](backend/CLAUDE.md) 與 [frontend/CLAUDE.md](frontend/CLAUDE.md) 各自深入。

## 專案概述

AI 驅動的證照考試備考 SaaS。前端 Next.js 15，後端 FastAPI，以 BDD E2E 測試驅動開發。

## 專案結構

| 路徑 | 說明 |
|------|------|
| `frontend/` | Next.js 前端（49 個 page.tsx, 32 個 API service） |
| `backend/` | FastAPI 後端（41 routers / 75 services / 52 models / 70 migrations） |
| `project/features/` | 44 個 Gherkin `.feature` 規格 |
| `project/specs/entity/erm.dbml` | **資料庫 SSOT**（57 張表） |

## 開發指令

### 前端
```bash
cd frontend
npm install
npm run dev          # http://localhost:3005
npm run build        # 靜態匯出
```

### 後端
```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload
.venv/bin/python -m behave tests/features/ --tags=~@ignore
```

**必須使用 `.venv/bin/python`（Python 3.13）**；系統 `python3` 是 3.9 不相容。BDD 測試需要 Docker 來啟 Testcontainers（PostgreSQL + pgvector）。

## 技術棧摘要

| 層級 | 技術 |
|------|------|
| 前端 | Next.js 15.4 + React 19.2 + TypeScript 5.9 + TailwindCSS 4.1 |
| 後端 | FastAPI + SQLAlchemy 2.0 + PostgreSQL 15 + pgvector + Alembic |
| AI | `google-genai`（統一入口）+ Anthropic + OpenAI + Voyage embedding |
| Auth | Firebase Google SSO + PyJWT HS256 |
| 測試 | Behave BDD + Testcontainers + FastAPI TestClient + Playwright |
| 部署 | GCP Cloud Run + Firebase Hosting + GitHub Actions |
| 金流 | 綠界 ECPay |

## 路徑別名

`@/*` → `frontend/` 根（例：`@/lib/api/services`）

## 重要模式

- **DBML 是 SSOT**：所有 SQLAlchemy 模型須與 `erm.dbml` 一致
- **API 前綴**：`/api/v1`；所有欄位 snake_case
- **Token 儲存**：`certimate_jwt_token`（Remember Me → localStorage，否則 sessionStorage）
- **靜態匯出**：前端所有頁面 `'use client'`，`output: 'export'`；動態路由以 `generateStaticParams()` stub + Firebase rewrites 處理
- **Secret Manager**：生產 API key 禁走 `--set-env-vars` 明文，必須經 Secret Manager 注入
- **RLS**：`resource_chunks`、`answers` 等啟用 RLS，tenant_id 預設 public_b2c
- **TDD 流程**：Schema Analysis → Step Template → Red（404）→ Green → Refactor
- **BDD Tag 分類**：每個 Scenario 須屬 `@backend` / `@frontend` / `@fullstack`；`backend/tests/features/` 禁含 `@frontend`，`project/features/` 禁含 `@backend`。**跨資料夾刪除任一側 Rule/Scenario 前，必須先確認對側 sibling 檔已涵蓋等義 spec（防 2026-04-27 ForceGraph 規格毀損事件重演）**。規則見 [docs/bdd/tag-conventions.md](docs/bdd/tag-conventions.md)，提交前跑 `python3 scripts/lint_feature_tags.py`

## 交付品質閘門（不可跳過）

所有技術交付物在報告「完成」前，**必須依序通過**：

### 1. 工程師自檢
- TypeScript 編譯零錯誤（`cd frontend && npx tsc --noEmit`）
- 後端 BDD 測試通過
- API 型別與後端回傳欄位一致（snake_case）

### 2. CTO Code Review
- 架構符合 FastAPI / Pydantic v2 / SQLAlchemy / App Router pattern
- 錯誤處理完整（HTTPException、edge case）
- Feature File 同步（改變行為的程式碼必須更新 Scenario）

### 3. QA 架構師驗收（**不可省略**）
必過三層（見 memory `feedback_qa_three_layer_verification.md`）：
- **Layer 1 內容相關性**：UI 渲染資料必須與輸入對照正確，產出對照表
- **Layer 2 前端 UI 實測**：Chrome MCP 真實點擊按鈕驗證，禁用直接輸網址
- **Layer 3 空態區分**：空畫面必須查後端 job 表（`resource_parse_jobs` 等）+ Cloud Logging，不可目視判定「合理的空」

### 退回修正迴圈
```
工程師 → 自檢 → CTO Review → [通過] → QA 三層 → [通過] → 交付
                             → [退回] → 修正 → 自檢 → ...
```

## 科目隔離規則（不可違反）

知識節點必須嚴格隔離到所屬科目。細節與違規樣例見 [backend/CLAUDE.md](backend/CLAUDE.md)。

## 違規歷史（前車之鑑）

- **2026-04-13** 前端練習頁 API 欄位 `name` vs 型別 `label` 不一致，節點名稱全空；QA 三輪退回修正
- **2026-04-23** QA 判定「此資源尚無學習鷹架」為合理空態並簽核，實際 DB 裡 parse job 全部 `failed`（SDK 未安裝）；新增規則：空態必須查 job 表 failure_reason

## 重要參考

- 子目錄指引：[backend/CLAUDE.md](backend/CLAUDE.md)、[frontend/CLAUDE.md](frontend/CLAUDE.md)
- DBML SSOT：[project/specs/entity/erm.dbml](project/specs/entity/erm.dbml)
- Feature 規格：[project/features/](project/features/)
- Memory 規則：`~/.claude/projects/-Users-simon-certimate-project/memory/MEMORY.md`
