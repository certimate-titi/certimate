# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CertiMate is an AI-powered certificate exam preparation SaaS platform with a Next.js frontend and a Python (FastAPI) backend driven by BDD E2E tests.

## Repository Structure

- `frontend/` — Next.js application (UI)
- `backend/` — FastAPI backend (API + BDD E2E tests)
- `project/` — Business planning docs, market analysis, and BDD `.feature` specs
  - `project/specs/entity/erm.dbml` — **Single Source of Truth** for the database schema (DBML format, 38+ tables)
  - `project/features/` — Gherkin `.feature` files defining product requirements

## Development Commands

### Frontend (from `frontend/`)

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (uses .next-dev/ for dev builds)
npm run build        # Production build (static export to .next/)
npm run lint         # ESLint
npm run clean        # Clean Next.js cache
```

Environment variables: copy `.env.example` to `.env.local` and fill in `GEMINI_API_KEY`, `APP_URL`, `NEXT_PUBLIC_FIREBASE_API_KEY`.

### Backend (from `backend/`)

```bash
cd backend
pip install -r requirements.txt    # Install Python dependencies
python -m behave tests/features/   # Run all BDD E2E tests
python -m behave tests/features/ --tags=~@ignore   # Run only completed features
python -m behave tests/features/01-身分驗證.feature  # Run a specific feature
python -m uvicorn app.main:app --reload             # Start dev API server
```

Requires Docker for Testcontainers (PostgreSQL). No `.env` needed for tests — Testcontainers auto-provisions a PostgreSQL container.

## Architecture

### Tech Stack — Frontend
- **Framework**: Next.js 15 (App Router) with React 19, TypeScript (strict mode)
- **Styling**: TailwindCSS 4 + PostCSS
- **Auth/DB**: Firebase Auth + Firestore
- **AI**: Google Gemini API (`@google/genai`)
- **Deployment**: Firebase Hosting (static export via `output: 'export'`)
- **Animation**: Motion library
- **Charts**: Recharts

### Tech Stack — Backend
- **Framework**: FastAPI + Uvicorn
- **ORM/DB**: SQLAlchemy 2.0 + PostgreSQL (psycopg 3) + Alembic migrations
- **BDD Testing**: Behave + Testcontainers (PostgreSQL) + FastAPI TestClient
- **Auth**: PyJWT (HS256)

### Path Alias
`@/*` maps to the `frontend/` root (e.g., `@/lib/api/services`, `@/types`).

### Key Directories — Frontend (under `frontend/`)

| Path | Purpose |
|------|---------|
| `app/` | Next.js App Router pages — public, auth, exam workflow, dashboard, admin, super-admin |
| `components/` | Reusable React components (navbar, gamification, onboarding steps) |
| `lib/api/services.ts` | **API service layer** — all data operations go through here. Currently returns mock data; function signatures are the API contract for future backend integration |
| `lib/api/client.ts` | HTTP client setup |
| `lib/auth-context.tsx` | Auth state management (Firebase Auth + localStorage for demo mode) |
| `lib/onboarding-context.tsx` | Onboarding flow state |
| `types/models.ts` | Domain models (User, Document, Exam, Question, etc.) |
| `types/api.ts` | API request/response type contracts |
| `hooks/` | Custom React hooks |
| `firebase.ts` | Firebase initialization + admin audit logging |
| `firestore.rules` | Firestore security rules |

### Key Directories — Backend (under `backend/`)

| Path | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/core/config.py` | Settings, paths, JWT config |
| `app/core/deps.py` | Dependency injection (DB session, JWT auth) |
| `app/models/` | SQLAlchemy ORM models (derived from `erm.dbml`) |
| `app/repositories/` | Repository classes (SQLAlchemy DB access) |
| `app/services/` | Business logic services |
| `app/api/` | FastAPI routers (API endpoints) |
| `app/schemas/` | Pydantic request/response schemas |
| `alembic/` | Database migrations |
| `tests/features/` | Behave BDD feature files + step definitions |
| `tests/features/environment.py` | Testcontainers lifecycle (PostgreSQL + context init) |
| `tests/features/helpers/` | JWT helper, test utilities |
| `tests/features/steps/` | Step definitions organized by subdomain |
| `tests/features/steps/common_then/` | Shared Then steps (操作成功/失敗/錯誤訊息) |

### Backend Step Definition Organization

Step definitions follow Event Storming classification:
```
tests/features/steps/{subdomain}/
  ├── aggregate_given/   # DB entity setup (Given steps)
  ├── commands/          # HTTP API calls (When steps)
  ├── aggregate_then/    # DB state verification (Then steps)
  └── readmodel_then/    # API response verification (Then steps)
```

Each step is in its own file (one step per file pattern).

### Page Structure
- **Public**: landing (`/`), login, signup, forgot-password
- **Authenticated**: dashboard, onboarding, account
- **Exam workflow**: exam/setup → exam/workspace → exam/results
- **Features**: knowledge (mind map), review (error analysis)
- **Admin**: admin (institutional B2B), super-admin (platform-level with audit logs, user management, finance, moderation, settings)

### Domain Concepts
- **Subscription tiers**: FREE, PRO_199, PRO_PLUS_399, ULTRA_1599
- **Document sources**: PDF, Markdown, YouTube URL, handwritten image
- **Exam types**: mock exam, spaced repetition, flashcard set
- **Gamification**: streaks, achievements, daily quests, growth milestones

### Important Patterns — Frontend
- All pages are client-side rendered (`'use client'`) — the app is statically exported
- Auth context provides demo user support via localStorage alongside real Firebase Auth
- The service layer in `lib/api/services.ts` is the single source of truth for all API calls — when implementing backend integration, modify implementations here without changing function signatures
- HMR can be disabled via `DISABLE_HMR=true` env var (used in AI Studio)
- ESLint errors are ignored during builds (`ignoreDuringBuilds: true` in next.config.ts)

### Important Patterns — Backend
- **DBML is the Single Source of Truth** for the database schema (`project/specs/entity/erm.dbml`). All SQLAlchemy models must match the DBML definitions.
- **TDD workflow**: Schema Analysis → Step Template → Red (tests fail with HTTP 404) → Green (implement API) → Refactor
- **E2E tests use Testcontainers** — a real PostgreSQL container is spun up per test session, Alembic migrations applied, and tables truncated between scenarios
- **context** is used to pass state between Given/When/Then steps: `context.db_session`, `context.api_client`, `context.jwt_helper`, `context.ids`, `context.memo`, `context.last_response`
- **API prefix**: `/api/v1` — all endpoints are under this prefix
- **JSON field naming**: snake_case for all API request/response fields
- **No backend API in Red phase** — tests should fail with HTTP 404; API endpoints are added only in Green phase
- **Alembic migrations** are in `backend/alembic/versions/` — manually written since Docker may not be available for autogenerate

## Feature Specifications

BDD-style `.feature` files live in `project/features/` and define the product requirements (auth, resource upload, exams, knowledge map, review, admin, etc.). Reference these when implementing new features.

## BDD E2E Test Pipeline

The backend follows an automated BDD E2E pipeline for each `.feature` file:

1. **Schema Analysis** — Verify feature ↔ DBML consistency, create/update ORM models
2. **Step Template** — Generate behave step definition skeletons with TODO annotations
3. **Red** — Implement full step definitions + repositories (tests fail: HTTP 404)
4. **Green** — Implement FastAPI endpoints + services (tests pass)
5. **Refactor** — Improve code quality under test protection

Feature files are copied to `backend/tests/features/` for execution. The `@ignore` tag is removed after Red phase completion.
