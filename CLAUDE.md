# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CertiMate is an AI-powered certificate exam preparation SaaS platform. It's a **frontend-only** Next.js application deployed to Firebase Hosting, using Firebase Auth + Firestore for backend services and Google Gemini for AI features.

## Repository Structure

- `frontend/` — The Next.js application (all development happens here)
- `project/` — Business planning docs, market analysis, and BDD `.feature` specs

## Development Commands

All commands run from `frontend/`:

```bash
cd frontend
npm install          # Install dependencies
npm run dev          # Start dev server (uses .next-dev/ for dev builds)
npm run build        # Production build (static export to .next/)
npm run lint         # ESLint
npm run clean        # Clean Next.js cache
```

Environment variables: copy `.env.example` to `.env.local` and fill in `GEMINI_API_KEY`, `APP_URL`, `NEXT_PUBLIC_FIREBASE_API_KEY`.

## Architecture

### Tech Stack
- **Framework**: Next.js 15 (App Router) with React 19, TypeScript (strict mode)
- **Styling**: TailwindCSS 4 + PostCSS
- **Auth/DB**: Firebase Auth + Firestore
- **AI**: Google Gemini API (`@google/genai`)
- **Deployment**: Firebase Hosting (static export via `output: 'export'`)
- **Animation**: Motion library
- **Charts**: Recharts

### Path Alias
`@/*` maps to the `frontend/` root (e.g., `@/lib/api/services`, `@/types`).

### Key Directories (under `frontend/`)

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

### Important Patterns
- All pages are client-side rendered (`'use client'`) — the app is statically exported
- Auth context provides demo user support via localStorage alongside real Firebase Auth
- The service layer in `lib/api/services.ts` is the single source of truth for all API calls — when implementing backend integration, modify implementations here without changing function signatures
- HMR can be disabled via `DISABLE_HMR=true` env var (used in AI Studio)
- ESLint errors are ignored during builds (`ignoreDuringBuilds: true` in next.config.ts)

## Feature Specifications

BDD-style `.feature` files live in `project/features/` and define the product requirements (auth, resource upload, exams, knowledge map, review, admin, etc.). Reference these when implementing new features.
