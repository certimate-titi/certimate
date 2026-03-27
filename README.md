# CertiMate 證照考試學習平台

CertiMate 是一個整合 AI 技術的證照學習與考試資源平台。透過人工智慧自動化解析學習資料，生成心智圖、模擬考題與個人化複習計畫，成為使用者備考路上的最佳陪伴者。

---

## 核心功能

- **AI 資源解析** — 上傳 PDF、圖片或 YouTube 連結，由 AI 自動萃取重點並轉換為 Markdown 格式
- **知識心智圖** — 視覺化學習地圖，自動生成知識節點並提供導覽功能
- **模擬機考系統** — 根據學習內容自動生成符合考綱的模擬試題，提供即時回饋
- **錯題複習與 AI 教練** — 針對弱點進行 AI 引導式教學，結合遺忘曲線安排複習排程
- **訂閱與金流** — 多層級訂閱方案 (FREE / PRO / PRO+ / ULTRA)，整合綠界金流
- **B2B 機構管理** — 機構管理員批量管理學員、派發測驗與查看分析報表
- **平台管理後台** — 財務管理、內容審核、系統設定、異常維修管理
- **社群與關懷** — 成就系統、每週報告、意見反饋

---

## 技術架構

### Frontend
- **Framework**: Next.js 15 (App Router) + React 19 + TypeScript
- **Styling**: TailwindCSS 4 + ShadcnUI
- **Auth/DB**: Firebase Auth + Firestore
- **AI**: Google Gemini API (`@google/genai`)
- **Deployment**: Firebase Hosting (static export)

### Backend
- **Framework**: FastAPI + Uvicorn
- **ORM/DB**: SQLAlchemy 2.0 + PostgreSQL (psycopg 3)
- **Migrations**: Alembic (16 migrations, 42 tables)
- **Testing**: Behave BDD + Testcontainers (PostgreSQL) + FastAPI TestClient
- **Auth**: PyJWT (HS256)

### Development Methodology
- **TDD/BDD**: 25 feature files, 255 scenarios, 1549 steps — all passing
- **5-Phase Pipeline**: Schema Analysis -> Step Template -> Red -> Green -> Refactor

---

## 目錄結構

```
certimate/
├── frontend/               # Next.js 前端應用
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── lib/api/            # API service layer
│   └── types/              # TypeScript type definitions
├── backend/                # FastAPI 後端
│   ├── app/
│   │   ├── api/            # FastAPI routers (20+ endpoints)
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── repositories/   # Repository pattern (DB access)
│   │   ├── services/       # Business logic
│   │   ├── schemas/        # Pydantic schemas
│   │   └── core/           # Config, deps, auth
│   ├── alembic/versions/   # DB migrations (001-016)
│   └── tests/features/     # BDD E2E tests
│       ├── steps/          # Step definitions (25 subdomains)
│       ├── helpers/        # JWT helper, test utilities
│       └── *.feature       # 25 feature files
├── project/                # Business planning & specs
│   ├── features/           # Gherkin feature specifications
│   └── specs/entity/       # erm.dbml (database schema SSOT)
├── CLAUDE.md               # AI-assisted development guide
└── README.md               # This file
```

---

## 快速開始

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker (for Testcontainers)

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # Fill in API keys
npm run dev                   # http://localhost:3000
```

### Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload   # http://localhost:8000
```

### Run BDD Tests

```bash
cd backend
python -m behave tests/features/ --tags=~@ignore   # All completed features
python -m behave tests/features/01-身分驗證.feature  # Specific feature
```

Requires Docker running (Testcontainers auto-provisions PostgreSQL).

---

## Feature Coverage

| # | Feature | Scenarios |
|---|---------|-----------|
| 01 | 身分驗證 (Auth) | Registration, login, verification, roles |
| 02 | 資源上傳 (Resources) | PDF, Markdown, YouTube, handwritten |
| 03 | 知識心智圖 (Knowledge Map) | Generation + navigation |
| 04 | 測驗設定 (Exam Setup) | Configuration + AI generation |
| 05 | 模擬機考 (Mock Exam) | Timer, submission, scoring |
| 06 | 測驗結果 (Results) | Analytics, weak areas |
| 07 | 錯題複習 (Wrong Answers) | AI coaching, spaced repetition |
| 08 | 訂閱管理 (Subscription) | Plans, ECPay payment, permissions |
| 09 | 學習排程 (Schedule) | Ebbinghaus curve scheduling |
| 10 | B2B 管理 (Edu Console) | Institution management |
| 11 | 資源庫 (Resource Library) | Shared resource management |
| 12 | 平台管理 (Platform Admin) | Finance, moderation, settings |
| 13 | 儀表板 (Dashboard) | Progress, achievements, streaks |
| 14 | 社群關懷 (Community) | Engagement, proactive care |
| 15 | 引導流程 (Onboarding) | First-login guidance |
| 16 | 異常維修 (Anomaly) | Error tracking, maintenance |
| 17 | 意見反饋 (Feedback) | User feedback collection |

---

## License

(C) 2026 CertiMate Team. All Rights Reserved.
