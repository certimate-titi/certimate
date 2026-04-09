# TiTi (CertiMate) 專案追蹤文件

**報告日期**：2026-04-08
**報告人**：CEO 總指揮
**版本**：v1.0

---

## A. 專案健康指標

| 指標 | 數值 | 健康度 |
|------|------|--------|
| BDD Feature 規格 | 43 個 | -- |
| BDD 通過 Scenario | 497 / 734 (67.7%) | -- |
| 後端 API Router | 31 個 | -- |
| 後端 ORM Model | 40 個 | -- |
| 後端 Service | 48 個 | -- |
| Alembic Migration | 001-040 | -- |
| 前端頁面 | 29 個 | -- |
| 前端 API 整合 | 100% 真實 API（零 mock） | -- |
| 考古題已匯入 | 7,992 題 / 395 科目 | -- |
| 前端建置 | FAILING（TypeScript error） | -- |

---

## B. Feature 完成狀態矩陣

### B1. 已完成（BDD + API + Service 齊備）— 35 個

| # | Feature | BDD 狀態 | 前端 | 後端 |
|---|---------|----------|------|------|
| 01 | 身分驗證 | PASS（部分 fail） | 登入/註冊/忘記密碼 | auth router + service |
| 02 | 資源上傳 | PASS | 知識頁上傳 | resource router + service |
| 03 | 知識心智圖 | PASS（部分 error） | 心智圖頁 | knowledge_map router + service |
| 03a | 知識心智圖生成 | PASS | -- | ai_questions router |
| 03b | 知識心智圖導航 | PASS（部分 fail） | 心智圖導航 | knowledge_nav_service |
| 04 | 測驗設定 | PASS (25/25) | exam/setup 頁 | exam router + service |
| 04a | AI 考題生成服務 | ERROR（undefined steps） | -- | ai_question_service |
| 05 | 模擬機考 | ERROR（undefined steps） | exam/workspace 頁 | mock_exam_service |
| 06 | 測驗結果 | ERROR（undefined steps） | exam/results 頁 | exam_result_service |
| 07 | 錯題複習與 AI 教練 | ERROR（undefined steps） | review 頁 | wrong_answer + ai_coach |
| 08 | 訂閱管理 | PASS | pricing 頁 | subscription_service |
| 08a | 綠界金流串接 | PASS | -- | ecpay_service |
| 08b | 付款後權限更新 | PASS | -- | subscription_service |
| 09 | 學習記憶排程 | PASS | -- | schedule_service |
| 10 | B2B 機構管理後台 | PASS | edu-console 頁 | b2b_service |
| 11 | 資源庫管理 | PASS | -- | resource_library_service |
| 12 | 平台管理後台 | PASS | super-admin | admin_service |
| 12a | 財務管理 | PASS | super-admin/finance | admin_finance_service |
| 12b | 內容審核 | PASS | super-admin/moderation | admin_moderation_service |
| 12c | 系統設定 | PASS | super-admin/settings | admin_settings_service |
| 13 | 儀表板與成就 | PASS | dashboard 頁 | dashboard_service |
| 14 | 社群歸屬與關懷 | PASS | -- | community_service |
| 15 | 首次登入引導 | PASS（部分 fail） | onboarding 頁 | onboarding_service |
| 16 | 異常維修管理 | PASS | -- | anomaly_service |
| 17 | 意見反饋 | PASS | feedback 頁 | feedback_service |
| 18(定價) | 定價與升級引導 | PASS | pricing 頁 | pricing_service |
| 19 | 交錯練習 | PASS | -- | exam_service |
| 21 | 番茄鐘學習節奏 | PASS | -- | schedule_service |
| 23 | 考古題題庫管理 | PASS（部分 error） | -- | exam_service + HistoricalExam |
| 25 | AI 考題退場與放榜 | PASS | -- | retirement_service |
| 26 | 考綱逆向工程 | PASS | -- | reverse_engineering_service |
| 27 | 個人化錯題地圖 | PASS | -- | wrong_answer_map_service |
| 28 | 階層式難度遞進 | PASS | -- | difficulty_progression_service |
| 29 | 知識樹合併對齊 | PASS | -- | knowledge_merge_service |
| 30 | Prompt 模板管理 | PASS | super-admin/prompt-templates | prompt_template_service |

### B2. 部分完成（Step 有、缺 API/Service）— 3 個

| # | Feature | 缺少項目 | 影響 |
|---|---------|----------|------|
| 20 | 信心度校準 | 缺 API Router + Service | 有 step defs 但無後端 endpoint |
| 22 | 帳號設定與個人偏好 | 缺 API Router + Service | 前端 account 頁已有，後端空缺 |
| 31 | 多租戶安全與資料隔離 | 缺 API Router | Migration 038-040 已完成，缺獨立 router |

### B3. 僅有規格（無 Step 實作）— 2 個

| # | Feature | 說明 |
|---|---------|------|
| 18 | 題目分類與考試趨勢分析 | 有 feature 檔和 DBML，缺 step + service |
| 24 | 系統公告管理 | 有 feature 檔和 API router，缺 step defs |

---

## C. 進行中工作

| 項目 | 負責角色 | 狀態 | 備註 |
|------|----------|------|------|
| 考古題 112-113 年爬蟲 | 考題設計 | 80% | Catalog 已掃描，PDF 待下載 |
| Feature 31 BDD 測試驗證 | 測試工程師 | 待驗證 | Migration 完成，step 有但缺完整綠燈 |
| 前端建置修復 | 前端研發 | 阻塞中 | edu-console TypeScript error |

---

## D. 未開始工作

### D1. 基礎設施（運營工程師）

| 項目 | 優先級 | OKR 對齊 | 備註 |
|------|--------|----------|------|
| Redis 語意快取 | HIGH | O3-KR1 | LLM 成本控制必要 |
| OpenTelemetry 觀測性 | MEDIUM | O3 | 監控 + 告警 |
| Celery 任務佇列 | MEDIUM | O3 | OCR/STT 非同步處理 |
| CI/CD Pipeline | HIGH | O3 | GitHub Actions + 自動測試 |
| Production DB 備份策略 | MEDIUM | O3 | 災難復原 |

### D2. 安全（後端研發）

| 項目 | 優先級 | OKR 對齊 | 備註 |
|------|--------|----------|------|
| RLS 端點全面覆蓋 | HIGH | O2-KR1 | 見缺陷 S-1 |
| LLM Guardrail | MEDIUM | O3-KR1 | Prompt injection 防護 |
| 欄位加密（answers） | MEDIUM | O2 | B2B 合規要求 |
| Rate Limiting | MEDIUM | O3 | API 濫用防護 |

### D3. 功能（產品 + 研發）

| 項目 | 優先級 | OKR 對齊 | 涉及 Feature |
|------|--------|----------|-------------|
| 信心度校準 API | MEDIUM | O3-KR3 | Feature 20 |
| 帳號設定 API | MEDIUM | O2-KR3 | Feature 22 |
| 系統公告 Step | LOW | O2 | Feature 24 |
| 題目分類趨勢 | MEDIUM | O1-KR2 | Feature 18 |
| B2B 租戶 Provisioning 流程 | HIGH | O2-KR1 | Feature 31 延伸 |
| 考古題 Bloom 分類 | HIGH | O1-KR3 | AI 批次處理 |

### D4. 前端（前端研發）

| 項目 | 優先級 | 備註 |
|------|--------|------|
| 修復 build error | CRITICAL | edu-console TypeScript |
| Segment-level Error Boundaries | HIGH | 目前只有全域 error.tsx |
| Firebase config 移出 git | HIGH | API key 曝露 |
| .env.example 補齊 | MEDIUM | 缺 NEXT_PUBLIC_API_URL |
| 移除 `as any` / `as unknown` | MEDIUM | 11 處不安全型別轉換 |

---

## E. 缺陷分析報告

### E1. CRITICAL（必須立即修復）

| ID | 缺陷 | 檔案 | 說明 |
|----|------|------|------|
| C-1 | 前端 build 失敗 | `app/edu-console/student/[id]/page.tsx:270` | `Promise.allSettled` 型別推斷錯誤，`.error` 屬性不存在 |
| C-2 | SQL Injection 風險 | `app/scripts/purge_tenant_data.py` | f-string 插入表名/欄位名進 SQL，應改用 SQLAlchemy identifiers |

### E2. HIGH（本週應修復）

| ID | 缺陷 | 檔案 | 說明 |
|----|------|------|------|
| H-1 | 多租戶 RLS 未全面覆蓋 | `app/api/knowledge_map.py` 等 | RLS-sensitive 端點使用 `get_db` 而非 `get_db_with_tenant`，可能跨租戶存取 |
| H-2 | DBML 與 ORM 不一致 | 全域 | DBML 定義 ~48 表，ORM 只有 40 個模型。缺少：Achievement, DailyQuest, Streak, AdminRole, PromptAbTest 等 |
| H-3 | Firebase API Key 寫死在 git | `frontend/firebase-applet-config.json` | 雖然 Firebase key 是公開的，但不應進版控 |
| H-4 | SSRF 白名單邏輯缺陷 | `app/core/security.py:103-110` | 白名單域名跳過 IP 檢查，應始終驗證 resolved IP |

### E3. MEDIUM（兩週內修復）

| ID | 缺陷 | 檔案 | 說明 |
|----|------|------|------|
| M-1 | Service 繞過 Repository | 多個 service | `weekly_report_service.py` 等直接 `db.query()`，違反分層 |
| M-2 | 異常吞嚥 | `ai_generation_service.py` | 寬泛 `except Exception` + 返回 `None`，掩蓋 bug |
| M-3 | 錯誤回應不一致 | 多個 service | 部分用 dict `{"error": True}`，部分用 `HTTPException` |
| M-4 | 快取清除是空殼 | `admin_settings_service.py:400` | `clear_cache()` 只記 audit log，不實際清快取 |
| M-5 | PUBLIC_B2C_TENANT_ID 散布 | `deps.py`, `tenant_repository.py`, `import_exam_questions.py` | UUID 寫死在多處，應集中管理 |
| M-6 | 前端 11 處不安全型別轉換 | `knowledge/page.tsx` 等 | `as unknown as X` 暗示 API 回應與 TypeScript 型別不匹配 |
| M-7 | 前端缺 Error Boundary | 全域 | 只有 `app/error.tsx`，無 segment-level boundary |
| M-8 | .env.example 不完整 | `frontend/.env.example` | 缺少 `NEXT_PUBLIC_API_URL` 文件 |

### E4. LOW（持續改善）

| ID | 缺陷 | 說明 |
|----|------|------|
| L-1 | JWT algorithm 未驗證 | `settings.JWT_ALGORITHM` 未限定安全算法，理論上可被設為 "none" |
| L-2 | 測試 seed data 寫死 | `environment.py` 的 plan quota 與 tenant ID 硬編碼 |
| L-3 | 前端 ESLint 跳過 | `ignoreDuringBuilds: true` 導致 lint 問題不被發現 |
| L-4 | Zod 已安裝未使用 | 前端有 zod dependency 但未用於 API 回應驗證 |

---

## F. 架構設計不合理之處

### F1. Service 層過度膨脹（48 個）

**問題**：48 個 service 對 15 個 repository，比例 3.2:1。多數 service 直接操作 `db.query()`，Repository 層形同虛設。

**建議**：
- 簡單 CRUD 操作直接由 Repository 處理
- Service 只負責跨 Repository 的業務邏輯
- 或放棄 Repository 層，統一在 Service 中操作 DB

### F2. BDD Step 重複問題

**問題**：`ai_gen` 和 `exam` 兩個子領域有 36 個重複 step definition。已在 `__init__.py` 中 workaround（只 import 一方），但根因是兩個子領域邊界定義不清。

**建議**：合併 `ai_gen` 到 `exam` 子領域，或明確劃分：
- `exam` = 使用者考試流程
- `ai_gen` = AI Pipeline 內部邏輯

### F3. 前端 API Mock 與真實 API 切換無機制

**問題**：前端已 100% 使用真實 API，但沒有 MSW (Mock Service Worker) 或 feature flag 機制。開發者離線時無法開發前端。

**建議**：保留 MSW 作為開發模式，透過 env var 切換。

### F4. 考古題架構分裂

**問題**：三種題目來源，但資料架構不統一：
1. `data/historical_questions/ipas/` — 舊格式 JSON
2. `data/historical_questions/114010/` — 新爬蟲格式 JSON
3. `data/historical_questions/finance/`, `real_estate/` — 另一種格式

**建議**：統一 JSON schema，所有來源都走 `historical_exams` + `questions` 表。

### F5. Migration 累積風險

**問題**：40 個 migration 檔案，每次部署需要從頭跑。Production 環境若從零開始，需要 40 步遷移。

**建議**：定期產生 "squash migration"（合併前 N 個 migration 為一個 baseline）。

---

## G. OKR 進度追蹤

| 目標 | KR | 當前狀態 | 阻塞因素 |
|------|-----|---------|----------|
| O1 最強 AI 出題引擎 | KR1 正確率 >= 95% | 未測量 | AI Pipeline step 未實作完整 |
| | KR2 出卷 <= 30 min | 未測量 | 7,992 考古題已入庫，待 UI 整合 |
| | KR3 信度 100% | 部分 | 考古題標 historical，AI 題未標 |
| O2 200 付費用戶 | KR1 B2B 上線 | 待完成 | Feature 31 BDD 待驗證 |
| | KR2 轉換率 >= 8% | 未開始 | 需上線後追蹤 |
| O3 成本控制 | KR1 LLM <= 15% | 未開始 | Redis 快取未建立 |
| | KR2 月均 4 次模考 | 未測量 | 需上線後追蹤 |

---

## H. 建議行動（優先序）

### 本週必做

1. **修復前端 build** — edu-console TypeScript error（C-1）
2. **修復 SQL injection** — purge_tenant_data.py（C-2）
3. **RLS 覆蓋補齊** — 所有 answer/resource_chunk 端點（H-1）

### 下兩週

4. **DBML ↔ ORM 對齊** — 補齊缺少的 5+ 模型（H-2）
5. **Feature 20/22 API 實作** — 信心度校準 + 帳號設定
6. **Firebase config 移出 git**（H-3）
7. **統一錯誤處理模式**（M-3）

### 本月

8. **CI/CD Pipeline** — GitHub Actions
9. **Redis 語意快取** — LLM 成本控制
10. **考古題 112-113 年完整匯入**
11. **AI Bloom 分類批次處理**
12. **B2B 租戶 provisioning 流程**

---

*文件位置*：`project/TiTi_ProjectTracker_20260408.md`
*下次更新*：2026-04-15（週報時間）
*維護者*：CEO 總指揮
