# 代辦項目及處理程序紀錄

## 待辦事項

### 📌 7. Prompt 模板管理 — BDD 測試與前後端實作

**後端 BDD E2E 測試（依 TDD 流程）：**

1. **Schema Analysis** — 驗證 Feature 30 與 DBML 一致性，建立/更新 ORM 模型（`prompt_template.py`、`prompt_template_version.py`、`prompt_ab_test.py`）
2. **Alembic Migration** — 建立 migration 新增 `prompt_templates`、`prompt_template_versions`、`prompt_ab_tests` 三張表
3. **Step Template** — 生成 `tests/features/steps/prompt_template/` 下的 step definition 骨架
4. **Red（紅燈）** — 實作完整 step definitions + repositories，測試以 HTTP 404 失敗
5. **Green（綠燈）** — 實作 FastAPI endpoints（`app/api/prompt_template.py`）+ services（`app/services/prompt_template_service.py`），測試全部通過
6. **Seed 腳本** — 實作 `app/scripts/seed_prompts.py`，從 `03_Prompt_Templates/` 同步至 DB
7. **Refactor** — 在測試保護下改善程式碼品質

**前端實作：**

8. **管理後台 — Prompt 模板列表頁** — `/admin/prompt-templates`，支援分類篩選、啟用/停用切換
9. **管理後台 — Prompt 模板編輯頁** — 即時編輯 system_prompt / user_prompt / temperature，儲存後自動版本++
10. **管理後台 — 版本歷史與回滾** — 版本對比 diff view、一鍵回滾
11. **管理後台 — A/B 測試管理** — 建立測試、設定流量比例、查看指標、結束選勝者

---

## 完成事項

### ✅ 1. 題目分類 — 完成於 2026-04-02
考古題分析時需進行該科目的題目分類佔比讓模擬考試能有不同難度以及更符合考試趨勢
- 記憶類別 / 理解類別 / 應用類別 / 分析類別 / 評估類別 / 創造類別（Bloom's Taxonomy）

**處理結果**：
- 更新 `project/specs/entity/erm.dbml`：新增 `bloom_category` enum、`questions.bloom_category`、`exams.bloom_distribution`
- 新增 `project/features/18-題目分類與考試趨勢分析.feature`

**待手動執行**：Alembic migration 017、ORM 模型更新、前端圖表

---

### ✅ 2. 考古題爬蟲 — 完成於 2026-04-02
依照台灣證照市場概況與題庫公開程度建立爬蟲 SKILL，優先級：金融 🏆A > 不動產 🏆A > iPAS 🥈B

**處理結果**：
- 新增 `.claude/skills/exam-crawler/SKILL.md`（包含爬蟲策略、Bloom 分類 Prompt、標準輸出 JSON schema）

**待手動執行**：實作 `backend/scripts/crawlers/` 爬蟲腳本、管理後台匯入 API

---

*詳細處理紀錄：`docs/todo-processing-2026-04-02T10-00-00.md`*

---

### ✅ 3. Edu 學生訂閱衝突處置 — 完成於 2026-04-06

Edu 學生若已有個人訂閱方案（PRO_199/PRO_PLUS_399），被機構指派 EDU 後的處置方式。

**決議：** 個人訂閱自動「暫停計費」（suspended），EDU 期間以 EDU 方案權益為主；EDU 結束後個人訂閱自動恢復，下次扣款日從恢復日重算。

**處理結果：**
- 更新 `project/features/08-訂閱管理.feature`：新增「EDU 學生既有訂閱衝突處置」章節（4 個 scenarios）

---

### ✅ 4. Edu 學生邀請信密碼設定流程 — 完成於 2026-04-06

Edu 學生收到邀請信點擊連結後，應先進入密碼設定頁，再完成帳號啟用。

**決議：** 邀請連結導向 `/invite/setup-password?token={token}`，密碼設定完成後帳號啟用並導向儀表板。Token 有效期 72 小時。

**處理結果：**
- 更新 `project/features/01-身分驗證.feature`：新增「EDU 學生邀請啟用流程」章節（5 個 scenarios）

---

### ✅ 6. Prompt 模板管理 — DBML + Feature 規格 — 完成於 2026-04-06

將 17 個 LLM Prompt 模板納入 DB 管理，支援版本控制、回滾、A/B 測試、Seed 同步。

**處理結果：**
- 更新 `project/specs/entity/erm.dbml`：新增 `prompt_category`、`ab_test_status` enum + `prompt_templates`、`prompt_template_versions`、`prompt_ab_tests` 3 張表
- 新增 `project/features/30-Prompt模板管理.feature`：10 個 Rule、20+ 個 Example（權限、CRUD、版本管理、回滾、A/B 測試、Seed 同步、by-plan 支援）
- 同步至 `backend/tests/features/30-Prompt模板管理.feature`

**前置完成項：**
- `project/03_Research_and_Development/03_Prompt_Templates/` 資料夾（17 個模板 .md 檔 + README）

**待手動執行：** Alembic migration、ORM 模型、seed 腳本 (`app.scripts.seed_prompts`)、管理後台 UI

---

### ✅ 5. feature_conflicts.md 決議事項處理 — 完成於 2026-04-06

feature_conflicts.md 中標註需 /titi-commander 評估的衝突項目（衝突1次數限制、衝突4更新時機、衝突7功能確認、問題8雙條件、問題9術語、問題10作答觸發）。

**處理結果：**
- 更新 `docs/feature_conflicts.md`：補全 6 個 CEO 決議
- 詳見 `docs/todo-processing-2026-04-06T01-08-22.md`