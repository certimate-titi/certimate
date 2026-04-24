# CertiMate / TiTi

AI 驅動的證照考試備考 SaaS 平台。使用者上傳教材或考古題，平台自動產生知識心智圖、學習鷹架、模擬考題與個人化複習排程。

- 前端：Next.js 15 + React 19，部署 Firebase Hosting（`certimate-titi.web.app`）
- 後端：FastAPI + PostgreSQL + pgvector，部署 Cloud Run（`asia-east1`）
- AI：Gemini 2.5 Pro / Claude / OpenAI 多廠商，Voyage embedding；雙 LLM 交叉驗證出題

---

## 核心功能

| 模組 | 說明 |
|------|------|
| 資源解析 Pipeline | 上傳 PDF / Markdown / 圖片 / YouTube → Gemini 多模態解析 → 自動產生學習鷹架（重點摘要 / 延伸思考 / 學習策略）+ T1/T2/T3 候選題 |
| 知識心智圖 | 自動從資源萃取知識節點、映射題目、合併跨資源節點、考綱逆向工程 |
| 模擬機考 | 階層難度遞進、信心度校準、交錯練習、番茄鐘模式、KaTeX 數學公式 |
| 錯題地圖 + AI 教練 | 個人化錯題可視化 + AI 引導 + 配額控制 + 艾賓浩斯遺忘曲線排程 |
| 訂閱 / 金流 | FREE / PRO_199 / PRO_PLUS_399 / ULTRA_1599 / EDU，整合綠界 ECPay |
| B2B 機構管理 | 學員分組、派發測驗、早期預警、週報 |
| 平台管理後台 | 使用者 / 財務 / 審核 / 稽核日誌 / 系統公告 / 異常維修 / Prompt 模板版控 |

---

## 技術棧

### 前端
- Next.js 15.4 (App Router, 靜態匯出) + React 19 + TypeScript 5.9
- TailwindCSS 4.1 + Motion + Recharts + Lucide
- Firebase Auth（Google SSO）+ JWT Bearer
- 靜態匯出模式，以 Firebase rewrites 對應動態路由

### 後端
- FastAPI + Uvicorn + Python 3.13
- SQLAlchemy 2.0 + PostgreSQL 15 + pgvector + Alembic
- Behave BDD + Testcontainers
- Google Cloud：Cloud Run、Cloud SQL、GCS、Secret Manager、BigQuery（Billing Export）

### AI / RAG
- `google-genai` SDK（統一入口）、Anthropic SDK、OpenAI SDK
- Voyage embedding + pgvector RAG
- 四階段考題生成 Pipeline + 雙 LLM 交叉驗證

---

## 目錄結構

```
project/
├── frontend/               Next.js 前端（49 個 page.tsx）
├── backend/                FastAPI 後端（41 routers / 75 services / 52 models）
│   ├── app/
│   ├── alembic/versions/   資料庫遷移 001–070
│   ├── data/historical_questions/   爬蟲產出 JSON
│   └── tests/features/     49 個 BDD feature
├── project/
│   ├── features/           44 個 Gherkin 規格
│   └── specs/entity/erm.dbml   資料庫 SSOT（57 張表）
├── README.md
└── CLAUDE.md               AI 協作開發指引
```

---

## 快速開始

### 前置
- Node.js 18+ / Python 3.13 / Docker（BDD 需 Testcontainers）

### 前端
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev                 # http://localhost:3005
```

### 後端
```bash
cd backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload   # http://localhost:8000
```

### BDD
```bash
cd backend
.venv/bin/python -m behave tests/features/ --tags=~@ignore
```

demo 登入：`admin@certimate.com` / `admin123`

---

## 生產部署

- 主幹推送到 `main` 觸發 GitHub Actions：
  - 後端 → Cloud Run service `certimate-titi` + Cloud SQL migration
  - 前端 → Firebase Hosting
- 祕密經 Secret Manager 注入（`gemini-api-key`、`anthropic-api-key`、`voyage-api-key`）
- 每次部署 commit hash 寫入 `BUILD_COMMIT` 環境變數

---

## 授權

© 2026 CertiMate Team
