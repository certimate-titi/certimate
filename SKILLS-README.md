# AIBDD Skills 功能說明文件

本文件說明 `.claude/skills/` 目錄下所有可用的 Claude Code Skills，依功能類別分組。

---

## 目錄

- [總覽](#總覽)
- [規格探索與建模 (Discovery & Spec)](#規格探索與建模-discovery--spec)
- [前端自動化 (Frontend)](#前端自動化-frontend)
- [Java E2E 測試自動化](#java-e2e-測試自動化)
- [Python E2E 測試自動化](#python-e2e-測試自動化)
- [Python Unit Test 自動化](#python-unit-test-自動化)
- [通用工具 (Utilities)](#通用工具-utilities)
- [TDD 階段流程說明](#tdd-階段流程說明)
- [ISA Gherkin Handler 對照表](#isa-gherkin-handler-對照表)

---

## 總覽

所有 Skills 遵循 **AI-BDD (AI-driven Behavior-Driven Development)** 方法論，從需求探索到自動化測試形成完整工作流程：

```
kickoff → discovery → (activity / feature / api / entity)-spec → starter → control-flow
                                                                              ↓
                                                          schema-analysis → step-template → red → green → refactor
```

| 標記 | 意義 |
|------|------|
| `/skill-name` | 可由使用者直接呼叫 (user-invocable) |
| `(internal)` | 僅供其他 Skill 內部呼叫 |

---

## 規格探索與建模 (Discovery & Spec)

### `/aibdd.kickoff`
**專案初始化引導。** 透過互動式 Q&A 篩選技術堆疊與測試策略，自動推導慣例路徑，產出 `specs/arguments.yml`。取代手動填寫大量參數。
- 參數：`[project-root]`

### `/aibdd.discovery`
**規格探索的主入口。** 以兩階段模式（Strategic / Tactical）統一協調所有規格視圖，任何回答均可能觸發跨視圖更新或 Strategy Guard 回退。始終保持 `.activity`、`.feature`、`api.yml`、`erm.dbml` 四個視圖的一致性。
- 參數：`--arguments --idea`

### `/aibdd.form.activity-spec`
**Activity 視圖的 Spec Skill。** 從 idea 生成 `.activity` 骨架並連動生成所有綁定檔案（`.feature`/`.md`）骨架，不確定處標記便條紙。可被 `/discovery` 調用，也可獨立使用。
- 參數：`[idea]`

### `/aibdd.form.feature-spec`
**Feature 視圖的 Spec Skill。** 從 `.feature` 骨架（含便條紙）、ES spec 或 User idea 出發，澄清並產出完整的 Gherkin Feature File。可被 `/discovery` 調用，也可獨立使用。
- 參數：`[feature-skeleton-or-idea]`

### `/aibdd.form.api-spec`
**API 視圖的 Spec Skill。** 從完整的 `.feature` 文件推導 OpenAPI 格式的 `api.yml`。每個 Feature 對應一個 endpoint。可被 `/discovery` 調用，也可獨立使用。
- 參數：`[FEATURE_SPECS_DIR]`

### `/aibdd.form.entity-spec`
**Entity 視圖的 Spec Skill。** 從完整的 `.feature` 文件推導 DBML 格式的 `erm.dbml`（資料模型）。Feature 的 Background datatable 對應資料表，Rule 對應約束，Aggregate 共現對應關聯。可被 `/discovery` 調用，也可獨立使用。
- 參數：`[FEATURE_SPECS_DIR]`

---

## 前端自動化 (Frontend)

技術堆疊：**Next.js 15 (App Router) + React 19 + TypeScript 5 (strict) + TailwindCSS 4 + Firebase (Auth + Firestore) + Google Gemini AI**

核心慣例：
- 無 `src/` 目錄，直接使用根層級 `app/`、`components/`、`lib/`、`types/`、`hooks/`
- 路徑別名 `@/*` → 專案根目錄
- 所有頁面 `'use client'`（static export 模式，無 Server Components）
- 型別使用純 TypeScript interface（無 Zod）
- API 服務層為單一檔案 `lib/api/services.ts`（mock data，函式簽名即 API 契約）
- 樣式：TailwindCSS 4 + `cn()` (clsx + tailwind-merge) + `cva()` (class-variance-authority)
- 圖示：`lucide-react`｜動畫：`motion`｜圖表：`recharts`｜表單：`react-hook-form`

### `/aibdd.auto.frontend.apifirst.msw.starter`
**Frontend Walking Skeleton 初始化。** 從 `templates/` 讀取所有樣板檔案，填入專案參數後輸出到專案目錄，建立 Next.js 15 + Firebase + Mock Services 的前端骨架。包含 App Router 頁面結構、Firebase 初始化、Auth Context、API Client（自動注入 Firebase Auth Bearer token）、TailwindCSS 4 設定。
- 參數：`[project-root]`

### `/aibdd.auto.frontend.msw-api-layer`
**前端 Stage 1：型別定義與 Mock Services 生成。** 從 `api.yml` + discovery features 產出：
- `types/models.ts`（Domain Models — 純 TypeScript interface）
- `types/api.ts`（API Request/Response 契約）
- `lib/api/services.ts`（單一檔案 Mock Services，函式簽名即 API 契約）
- Mock 資料來自 `.feature` 的具體 Given 步驟，不隨意編造
- 參數：`[specs-root-dir] [project-root]`

### `/aibdd.auto.frontend.nextjs-pages`
**前端 Next.js 頁面實作。** 基於已完成的 Walking Skeleton（Firebase + services.ts mock）和 UI/UX consultant 產出的 `layout.html` 靜態原型，將靜態頁面轉換為動態 Next.js React 元件。流程：參數載入 → 規格校驗 → 盤點頁面 → 元件拆解 → 逐頁實作 → 整合驗證。搭配三份參考文件：
- `references/spec-validation.md` — 規格校驗規則
- `references/component-decomposition.md` — 元件拆解策略（TailwindCSS 4 + cn() + cva()）
- `references/spec-driven-patterns.md` — Feature → UI 元素對照（react-hook-form 表單、useAuth() 權限）

### `/aibdd.frontend.e2e.activity-testplan`
**前端瀏覽器驗收測試計畫生成。** 從 Activity Diagram（`.activity` 檔案）+ 網頁 UI 推導出瀏覽器外部驗收測試計畫。Activity Diagram 提供流程組織與情境組織；網頁 UI 提供具體的 UI 測試行為細節。產出為 Markdown 格式的測試計畫，供 AI 透過瀏覽器進行自動化外部驗收。

---

## Java E2E 測試自動化

技術堆疊：**Spring Boot 3.2 + JPA + Cucumber 7.15 + Testcontainers**

### `/aibdd.auto.java.e2e.starter`
**Walking Skeleton 初始化。** 從 `templates/` 讀取樣板檔案，建立完整的 Spring Boot + JPA + Cucumber + Testcontainers 骨架。
- 參數：`[project-root]`

### `/aibdd.auto.java.e2e.control-flow`
**全自動批次迴圈。** 掃描 features 目錄，為每個 `.feature` 展開完整的 5 phase TODO 清單（schema-analysis → step-template → red → green → refactor），然後逐一執行直到全數完成。
- 參數：`[features-dir]`

### `/aibdd.auto.java.e2e.schema-analysis`
**Stage 0：Schema-First 分析。** 確認 Feature File 與 DBML 一致，JPA Entities 與 DBML 一致，Flyway Migration 已套用。GO/NO-GO 決策。
- 參數：`[feature-file]`

### `/aibdd.auto.java.e2e.step-template`
**Stage 1：Step Definition 樣板生成。** 從 Gherkin Feature 生成 Cucumber Step Definition 樣板。使用 Cucumber Expressions、`@Autowired` DI、ScenarioContext。
- 參數：`[feature-file]`

### `/aibdd.auto.java.e2e.red`
**Stage 2：紅燈生成器。** 將 Step Definition 樣板轉換為完整 E2E 測試程式碼 + JPA Entity + Spring Data JPA Repository。預期失敗：HTTP 404。
- 參數：`[feature-file]`

### `/aibdd.auto.java.e2e.green`
**Stage 3：綠燈階段。** Trial-and-error 循環讓測試通過，實作後端 API（DTO → Service → Controller → 路由註冊）。
- 參數：`[feature-file]`

### `/aibdd.auto.java.e2e.refactor`
**Stage 4：重構階段。** 在測試保護下改善程式碼品質，小步前進，嚴格遵守 code-quality 規範。
- 參數：`[feature-file]`

### `aibdd.auto.java.code-quality` (internal)
**程式碼品質規範合集。** 包含 SOLID 設計原則、Step Definition 組織規範、StepDef Meta 註記清理、日誌實踐、程式架構、程式碼品質等六項規範。供 refactor 階段嚴格遵守。

### Java E2E ISA Handlers (internal)

| Handler | 用途 |
|---------|------|
| `handlers.aggregate-given` | 資料庫實體建立（測試前置系統狀態設立） |
| `handlers.aggregate-then` | 驗證資料庫中應存在某實體資料 |
| `handlers.command` | 撰寫 API 呼叫步驟（When ... call table） |
| `handlers.query` | 撰寫 Query API 呼叫步驟 |
| `handlers.readmodel-then` | 驗證 API 的回應結果應該有什麼內容 |
| `handlers.success-failure` | 驗證操作成功或失敗 |

---

## Python E2E 測試自動化

技術堆疊：**FastAPI + SQLAlchemy + Behave + Testcontainers**

### `/aibdd.auto.python.e2e.starter`
**Walking Skeleton 初始化。** 從 `templates/` 讀取樣板檔案，建立完整的 FastAPI + SQLAlchemy + Behave + Testcontainers 骨架。
- 參數：`[project-root]`

### `/aibdd.auto.python.e2e.control-flow`
**全自動批次迴圈。** 掃描 features 目錄，為每個 `.feature` 展開完整的 5 phase TODO 清單（schema-analysis → step-template → red → green → refactor），然後逐一執行直到全數完成。
- 參數：`[features-dir]`

### `/aibdd.auto.python.e2e.schema-analysis`
**Stage 0：Schema-First 分析。** 確認 Feature File 與 DBML 一致，ORM Models 與 DBML 一致，GO/NO-GO 決策。
- 參數：`[feature-file]`

### `/aibdd.auto.python.e2e.step-template`
**Stage 1：Step Definition 樣板生成。** 從 Gherkin Feature 生成 Step Definition 樣板。識別事件風暴部位，指引對應的 Handler Prompt。
- 參數：`[feature-file]`

### `/aibdd.auto.python.e2e.red`
**Stage 2：紅燈生成器。** 將 Step Definition 樣板轉換為完整 E2E 測試程式碼 + SQLAlchemy Models + Repositories。預期失敗：HTTP 404。
- 參數：`[feature-file]`

### `/aibdd.auto.python.e2e.green`
**Stage 3：綠燈階段。** Trial-and-error 循環讓測試通過，實作後端 API（schemas → services → controllers → 路由註冊）。
- 參數：`[feature-file]`

### `/aibdd.auto.python.e2e.refactor`
**Stage 4：重構階段。** 在測試保護下改善程式碼品質，小步前進，嚴格遵守 code-quality 規範。
- 參數：`[feature-file]`

### `aibdd.auto.python.code-quality` (internal)
**程式碼品質規範合集。** 包含 SOLID 設計原則、Step Definition 組織規範、StepDef Meta 註記清理、日誌實踐、程式架構、程式碼品質等六項規範。供 refactor 階段嚴格遵守。

### Python E2E ISA Handlers (internal)

| Handler | 用途 |
|---------|------|
| `handlers.aggregate-given` | 資料庫實體建立（測試前置系統狀態設立） |
| `handlers.aggregate-then` | 驗證資料庫中應存在某實體資料 |
| `handlers.command` | 撰寫 API 呼叫步驟（When ... call table） |
| `handlers.query` | 撰寫 Query API 呼叫步驟 |
| `handlers.readmodel-then` | 驗證 API 的回應結果應該有什麼內容 |
| `handlers.success-failure` | 驗證操作成功或失敗 |

---

## Python Unit Test 自動化

技術堆疊：**Behave + FakeRepository（純 Unit Test，無 DB、無 HTTP）**

### `/aibdd.auto.python.ut.starter`
**Walking Skeleton 初始化。** 從 `templates/` 讀取樣板檔案，建立 Behave + FakeRepository 的純 Unit Test 骨架。
- 參數：`[project-root]`

### `/aibdd.auto.python.ut.control-flow`
**全自動批次迴圈。** 掃描 features 目錄，為每個 `.feature` 展開完整的 4 phase TODO 清單（step-template → red → green → refactor），然後逐一執行直到全數完成。
- 參數：`[features-dir]`

### `/aibdd.auto.python.ut.step-template`
**Stage 1：Step Definition 樣板生成。** 從 Gherkin Feature 生成 Unit Test Step Definition 樣板。使用 `context.repos`/`context.services` 取代 `api_client`/`db_session`。
- 參數：`[feature-file]`

### `/aibdd.auto.python.ut.red`
**Stage 2：紅燈生成器。** 建立 FakeRepository（`NotImplementedError`）+ Service 介面（`NotImplementedError`）+ 完整 Step Definition。預期失敗：`NotImplementedError`。
- 參數：`[feature-file]`

### `/aibdd.auto.python.ut.green`
**Stage 3：綠燈階段。** 實作 FakeRepository（dict-based）+ Service 業務邏輯。Trial-and-error 循環直到測試通過。
- 參數：`[feature-file]`

### `/aibdd.auto.python.ut.refactor`
**Stage 4：重構階段。** Phase A（測試程式碼）→ 跑測試 → Phase B（生產程式碼）→ 跑測試。嚴格遵守 code-quality 規範，安全規則禁止未經許可的跨檔搬移。
- 參數：`[feature-file]`

### Python UT ISA Handlers (internal)

| Handler | 用途 |
|---------|------|
| `handlers.aggregate-given` | 資料庫實體建立（測試前置系統狀態設立） |
| `handlers.aggregate-then` | 驗證資料庫中應存在某實體資料 |
| `handlers.command` | 撰寫 API 呼叫步驟（When ... call table） |
| `handlers.query` | 撰寫 Query API 呼叫步驟 |
| `handlers.readmodel-then` | 驗證 API 的回應結果應該有什麼內容 |
| `handlers.success-failure` | 驗證操作成功或失敗 |

---

## 通用工具 (Utilities)

### `/clarify-loop`
**需求澄清互動工具。** 當細節有可能不夠充分時，用此 Skill 依序向用戶澄清需求。定義提問格式、回答處理、澄清紀錄與提問上限等互動規則。

### `/frontend-design`
**高品質前端介面設計。** 建立具有高設計品質的 production-grade 前端介面。適用於網頁元件、頁面、Landing Page、Dashboard、React 元件、HTML/CSS 排版等。產出創意、精緻的程式碼與 UI 設計，避免千篇一律的 AI 風格。

---

## TDD 階段流程說明

每個技術堆疊（Java E2E / Python E2E / Python UT）都遵循相同的 TDD 階段流程：

```
┌─────────────────────────────────────────────────────────┐
│  Stage 0: schema-analysis (E2E only)                    │
│  確認 Feature ↔ DBML ↔ ORM/JPA 一致性                    │
├─────────────────────────────────────────────────────────┤
│  Stage 1: step-template                                 │
│  從 .feature 生成 Step Definition 樣板                    │
├─────────────────────────────────────────────────────────┤
│  Stage 2: red (紅燈)                                     │
│  建立測試程式碼 + 基礎架構，預期失敗                         │
├─────────────────────────────────────────────────────────┤
│  Stage 3: green (綠燈)                                   │
│  實作業務邏輯，trial-and-error 直到測試通過                  │
├─────────────────────────────────────────────────────────┤
│  Stage 4: refactor (重構)                                │
│  在測試保護下改善品質，遵守 code-quality 規範               │
└─────────────────────────────────────────────────────────┘
```

使用 `control-flow` Skill 可自動串連所有階段，批次處理整個 features 目錄。

---

## ISA Gherkin Handler 對照表

ISA Handlers 是 internal Skills，用於在 `.isa.feature` 類型的 Gherkin 測試中處理不同的事件風暴部位：

| 事件風暴部位 | Handler | Gherkin 關鍵字 |
|-------------|---------|---------------|
| Aggregate 建立 | `aggregate-given` | Given（前置資料） |
| Aggregate 驗證 | `aggregate-then` | Then（資料庫驗證） |
| Command 呼叫 | `command` | When（API 呼叫） |
| Query 呼叫 | `query` | When（查詢 API） |
| ReadModel 驗證 | `readmodel-then` | Then（回應內容驗證） |
| 成功/失敗判定 | `success-failure` | Then（操作結果） |

這些 Handler 在三個技術堆疊（Java E2E、Python E2E、Python UT）中均有對應的實作，命名規則一致。
