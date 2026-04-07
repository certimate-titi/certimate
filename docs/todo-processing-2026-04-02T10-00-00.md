# 待辦事項處理紀錄

**執行時間**：2026-04-02 10:00:00 (UTC+8)
**執行者**：Certimate Commander（自動排程任務）
**觸發來源**：scheduled-task `check-todo`

---

## 處理摘要

本次從 `docs/ToDoList.md` 讀取到 **2 項待辦事項**，已全數完成處理。

---

## 待辦事項 1：題目分類

### 原始需求
考古題分析時需進行該科目的題目分類佔比，讓模擬考試能有不同難度以及更符合考試趨勢。分類採 Bloom's Taxonomy 六個認知層次：記憶 / 理解 / 應用 / 分析 / 評估 / 創造。

### Commander 判斷
此需求屬於 **資料模型 + AI生成流程 + 測驗結果** 三層改動，相關角色：研發（DB/API）+ 產品（Feature Spec）。

### 執行結果

**1. 更新資料庫 Schema（DBML SSOT）**
- 檔案：`project/specs/entity/erm.dbml`
- 新增 `Enum bloom_category`（6 個值：remember / understand / apply / analyze / evaluate / create）
- 在 `Table questions` 新增欄位：
  - `bloom_category bloom_category` — Bloom 認知層次分類
  - `historical_source varchar(255)` — 考古題來源標記
- 在 `Table exams` 新增欄位：
  - `bloom_distribution jsonb` — 記錄整場考試的 Bloom 分佈

**2. 新增 BDD Feature 規格**
- 檔案：`project/features/18-題目分類與考試趨勢分析.feature`
- 涵蓋情境：
  - Bloom 分佈統計查詢
  - 跨年度趨勢分析
  - AI 出題依趨勢配比（考試趨勢模式）
  - 測驗結果 Bloom 分析報告
  - 考古題批次匯入 + 自動 Bloom 分類

### 後續工作（需手動執行）
- 建立 Alembic migration（下一個編號：017）加入 `bloom_category` enum 與欄位
- 更新 `backend/app/models/` 中的 `Question` 和 `Exam` ORM 模型
- 更新 04a-AI考題生成服務 的 Prompt 邏輯加入 Bloom 分類步驟
- 前端測驗結果頁新增 Bloom 分析圖表

---

## 待辦事項 2：考古題爬蟲

### 原始需求
建立一個 SKILL，可以自動爬取台灣各類證照的考古題，並進行題目分類。優先順序：金融證照（A）> 不動產證照（A）> iPAS（B）。

### Commander 判斷
此需求屬於 **新增 Claude Skill + 後端批次工具**，相關角色：研發（爬蟲實作）+ Prompt 工程師（Skill 設計）。

### 執行結果

**1. 建立考古題爬蟲 Skill**
- 檔案：`.claude/skills/exam-crawler/SKILL.md`
- 涵蓋內容：
  - 三大類別爬蟲策略（TABF / 內政部 / iPAS）
  - 題目解析輸出格式（標準 JSON schema）
  - Bloom 自動分類 Prompt 設計
  - 匯入格式規範（符合 CertiMate questions 資料表）
  - 合法性注意事項（遵守 robots.txt，請求頻率限制）

### 後續工作（需手動執行）
- 實作 `backend/scripts/crawlers/` 目錄下的爬蟲腳本
  - `tabf_crawler.py` — 金融研訓院考古題
  - `realestate_crawler.py` — 不動產考古題
  - `ipas_crawler.py` — iPAS 考古題
- 建立管理後台 API：`POST /api/v1/admin/questions/import-historical`
- 在 BDD Feature 18 中新增對應的後端測試

---

## 檔案異動清單

| 異動類型 | 檔案路徑 | 說明 |
|----------|----------|------|
| 修改 | `project/specs/entity/erm.dbml` | 新增 bloom_category enum、questions.bloom_category、questions.historical_source、exams.bloom_distribution |
| 新增 | `project/features/18-題目分類與考試趨勢分析.feature` | Bloom 分類與考試趨勢分析 BDD 規格 |
| 新增 | `.claude/skills/exam-crawler/SKILL.md` | 考古題爬蟲 Skill 設計文件 |
| 修改 | `docs/ToDoList.md` | 將已完成事項移至「完成事項」區塊 |

---

## CEO 決策建議

1. **優先執行 Alembic migration 017**：DBML 已更新，需同步至 DB schema，避免後續開發分歧
2. **先做分類，再做爬蟲**：題目分類（待辦1）是平台核心能力，應先完成 BDD Green 階段後，再串接考古題爬蟲（待辦2）
3. **金融證照為首選爬蟲目標**：市場最大（30萬+考生），題庫公開完整，ROI 最高
