# 代辦項目及處理程序紀錄

## 待辦事項

（目前無待辦事項）

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