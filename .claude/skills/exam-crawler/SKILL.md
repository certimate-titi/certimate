---
name: exam-crawler
description: >
  台灣證照考古題爬蟲 Skill——自動爬取金融證照、不動產證照、iPAS、高普考等考古題，
  並依照 Bloom 認知層次（記憶/理解/應用/分析/評估/創造）進行題目分類，
  輸出標準化 JSON 供 CertiMate 題庫系統匯入。匯入後可選擇性串接 preseed-mindmaps
  skill 用本地端 Claude Code 當 LLM 批次預生知識節點樹（零 API 費用）。
  當使用者提到「考古題爬蟲」、「爬取考古題」、「題庫匯入」、「批次抓題」、「金融證照題庫」、
  「不動產考古題」、「iPAS 考題」、「高普考題庫」、「題目分類佔比」時，務必觸發此 skill。
---

# 考古題爬蟲 Skill (exam-crawler)

## 角色設定

你是 CertiMate 平台的 **考古題爬蟲工程師**。
你的工作：**指定證照類別 → 爬取考古題來源 → 解析題目 → Bloom 分類 → 輸出標準 JSON → 匯入資料庫**。

---

## 支援證照類別（優先順序）

| 優先級 | 類別 | 來源 | 備注 |
|--------|------|------|------|
| S | 高普考 | 考選部 `wwwq.moex.gov.tw` | 初等/高考三級/普考，選擇題為主 |
| A | 金融證照 | 台灣金融研訓院 (TABF) `cfp.tabf.org.tw` | 每年 30 萬+ 考生，全選擇題 |
| A | 不動產證照 | 內政部不動產資訊平台 | 不動產經紀人、地政士 |
| B | iPAS 經濟部 | 經濟部產業人才發展資訊網 `ipas.mepa.gov.tw` | AI 規劃師等新興科技類 |

---

## 現有爬蟲工具

位置：`backend/scripts/crawlers/`

| 工具 | 位置 | 說明 |
|------|------|------|
| `moex_simple.py` | `backend/scripts/crawlers/` | 高普考爬蟲（download + parse），支援 Unicode 選項標記 |
| `auto_catalog_generator.py` | `backend/scripts/crawlers/` | 自動探測考選部考試/類科/科目組合 |
| `normalize_json.py` | `backend/scripts/crawlers/` | 將舊格式 JSON（ipas/finance/real_estate）轉換為統一格式 |
| `claude_cli_converter.py` | `exam-bank/parsers/` | **PDF → JSON 轉換器**（Claude CLI，不需 API KEY） |
| `gemini_pdf_converter.py` | `exam-bank/parsers/` | PDF → JSON 轉換器（Gemini API，需 GEMINI_API_KEY） |
| `exam_catalog.yaml` | `backend/scripts/crawlers/` | 114 年考試目錄 |
| `exam_catalog_complete.yaml` | `backend/scripts/crawlers/` | 112-114 年完整目錄 |

匯入工具：`backend/app/scripts/import_exam_questions.py`

---

## 標準 JSON 輸出格式（SSOT）

所有爬蟲產出的 JSON **必須**符合此格式，供 `import_exam_questions.py` 匯入。

### import_meta 結構

```json
{
  "import_meta": {
    "source": "考選部考畢試題查詢平臺",
    "exam_code": "114010",
    "category_code": "501",
    "subject_code": "0101",
    "exam_name": "114年初等考試",
    "total_questions": 41,
    "questions_with_answer": 41,
    "bloom_distribution": null,
    "difficulty_distribution": null,
    "year": 114
  },
  "questions": [...]
}
```

**欄位說明**：

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `source` | string | 是 | 資料來源名稱 |
| `exam_code` | string | 是 | 考試代碼（6 位數字如 `114010`，或類型碼如 `FIN114`、`IPA109`、`REA112`） |
| `category_code` | string | 是 | 類科代碼（數字如 `501`，或英文如 `securities`、`big_data`） |
| `subject_code` | string | 是 | 科目代碼（數字如 `0101`，或檔名前綴如 `trust_regulations_session01`） |
| `exam_name` | string | 否 | 考試名稱（人類可讀） |
| `total_questions` | int | 是 | 題目總數 |
| `questions_with_answer` | int | 是 | 有答案的題目數 |
| `bloom_distribution` | object/null | 否 | Bloom 認知層次分佈統計 |
| `difficulty_distribution` | object/null | 否 | 難易度分佈統計 |
| `year` | int | 否 | 民國年 |

### exam_code 編碼規則

| 來源 | 格式 | 範例 |
|------|------|------|
| 高普考（考選部） | `{民國年}{考試類型}` | `114010`（初等）、`114080`（高普考） |
| 金融證照 | `FIN{民國年}` | `FIN114`、`FIN113` |
| 不動產 | `REA{民國年}` | `REA112`、`REA111` |
| iPAS | `IPA{民國年}` | `IPA114`、`IPA109` |

### question 結構

```json
{
  "question_number": 1,
  "content": "下列文句「」中的成語用法，何者正確？",
  "type": "single_choice",
  "option_a": "選項 A 內容",
  "option_b": "選項 B 內容",
  "option_c": "選項 C 內容",
  "option_d": "選項 D 內容",
  "correct_answer": "D",
  "explanation": "",
  "bloom_category": null,
  "source_type": "historical"
}
```

**欄位說明**：

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `question_number` | int | 是 | 題號（從 1 開始） |
| `content` | string | 是 | 題幹文字（支援 Markdown + KaTeX） |
| `type` | string | 是 | `single_choice` / `multiple_choice` / `fill_in` / `calculation` |
| `option_a` ~ `option_d` | string | 否 | 四個選項（選擇題必填） |
| `correct_answer` | string | 是 | 正確答案（`A`~`D`，複選用 `ACE` 等） |
| `explanation` | string | 否 | AI 解析（空字串 = 待生成） |
| `bloom_category` | string/null | 否 | Bloom 認知層次（`remember`/`understand`/`apply`/`analyze`/`evaluate`/`create`） |
| `source_type` | string | 否 | 固定為 `historical`（匯入時自動設定） |

---

## 工作流程

### Step 1 — 確認目標

```
請指定：
1. 證照類別（高普考 / 金融 / 不動產 / iPAS）
2. 科目名稱或年份範圍（如：114 年高普考、金融證照 113-114 年）
3. 排除條件（如：排除申論題科目）
```

### Step 2 — 爬取

**高普考（考選部）** — 使用現有工具：

```bash
cd backend

# 1. 掃描可用考試目錄（自動探測）
python3 scripts/crawlers/auto_catalog_generator.py --years 114

# 2. 下載 PDF
python3 scripts/crawlers/moex_simple.py download --config scripts/crawlers/exam_catalog_complete.yaml

# 3. 解析 PDF → JSON
python3 scripts/crawlers/moex_simple.py parse
```

**金融 / 不動產 / iPAS** — 根據來源網站設計爬蟲：

```python
import requests
import pdfplumber
# 爬取 → 解析 → 輸出標準 JSON
```

### Step 2.5 — PDF → JSON 轉換（Claude CLI 版）

使用本地 Claude Code CLI 將 PDF 考題轉換為標準 JSON（不需要 Gemini API KEY）：

```bash
cd exam-bank/parsers

# 轉換單一 PDF
python3 claude_cli_converter.py --pdf /path/to/exam.pdf

# 指定答案卷 PDF（高普考等分卷格式）
python3 claude_cli_converter.py --pdf Q_0101.pdf --answer-pdf S_0101.pdf

# 自訂輸出路徑
python3 claude_cli_converter.py --pdf exam.pdf --output ../backend/data/historical_questions/ipas/ai/exam.json

# 批次轉換所有未處理 PDF
python3 claude_cli_converter.py

# 只偵測內容類型（不轉換）
python3 claude_cli_converter.py --dry-run

# 忽略 manifest 強制重轉
python3 claude_cli_converter.py --force

# 跳過 4 層驗證（加速）
python3 claude_cli_converter.py --skip-validation
```

**轉換流程**：pymupdf 萃取 PDF 文字 → Stage 0 內容偵測（7 種類型）→ Claude CLI 結構化轉換 → MD 解析 → 答案匹配 → 4 層品質驗證 → 輸出標準 JSON

**特點**：
- 使用本地 Claude Code CLI（OAuth 登入），**不需要任何 API KEY**
- 輸出 JSON 格式與 Gemini 版 `gemini_pdf_converter.py` 完全一致
- 支援 7 種內容類型（exam/regulation/textbook/summary/formula/syllabus/general）
- 4 層品質驗證：結構完整性 / 答案覆蓋率 / Claude 抽樣覆核 / 統計異常偵測
- Manifest 機制（PDF fingerprint 避免重複轉換）

**與 Gemini 版比較**：

| 項目 | `gemini_pdf_converter.py` | `claude_cli_converter.py` |
|------|--------------------------|--------------------------|
| LLM | Gemini 2.5 Flash API | 本地 Claude Code CLI |
| 費用 | ~$0.005/份（API 計費） | $0（含在 Claude Code 訂閱） |
| PDF 讀取 | 原生 PDF 上傳 | pymupdf 文字萃取 |
| 速度 | 2-5 秒/份 | ~250 秒/份 |
| 答案正確率 | baseline | 100% 一致 |
| 需要 API KEY | 是（GEMINI_API_KEY） | 否（OAuth 登入） |

### Step 3 — 格式正規化

如果產出的 JSON 不符合標準格式，使用正規化工具：

```bash
python3 scripts/crawlers/normalize_json.py --dry-run    # 預覽
python3 scripts/crawlers/normalize_json.py              # 執行
```

### Step 4 — Bloom 認知層次分類（選填）

呼叫 AI 模型對每道題目進行分類：

```python
BLOOM_CLASSIFICATION_PROMPT = """
請分析以下考試題目，判斷其認知層次（Bloom's Taxonomy）：

題目：{question_content}

分類標準：
- remember（記憶）：需要背誦、回想特定知識點
- understand（理解）：需要解釋、詮釋概念
- apply（應用）：需要將知識用於具體情境
- analyze（分析）：需要拆解、比較、找出關聯
- evaluate（評估）：需要評判、做出決策
- create（創造）：需要整合知識提出解方

只回傳分類名稱，不附說明。
"""
```

分類完成後更新 JSON 中每題的 `bloom_category` 和 `import_meta.bloom_distribution`。

### Step 5 — 匯入資料庫

```bash
cd backend

# Dry-run（預覽）
.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions --dry-run

# 正式匯入
.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions

# 僅匯入特定考試
.venv/bin/python -m app.scripts.import_exam_questions --json-dir data/historical_questions --exam-code 114010
```

匯入會自動：
- 建立 `historical_exams` 記錄（依 exam_code + category_code + subject_code 去重）
- 建立 `questions` 記錄（`exam_id=NULL`, `historical_exam_id=<對應 ID>`）
- 跳過已存在的題目（依 historical_exam_id + question_number 去重）

### Step 6 — （可選）預生知識節點心智圖 → 串接 `preseed-mindmaps` skill

匯入完考古題後，**強烈建議**立刻串接 `preseed-mindmaps` skill 把心智圖預生好，這樣使用者第一次選科目時就能立即看到節點樹，**不需要任何 LLM API 呼叫**。

**為什麼放在爬蟲 skill 尾端**：
- 考古題是靜態資料，匯入完後結構就固定了
- 心智圖節點樹跟考古題內容 1:1 對應，批次預生比 on-demand 合適
- 走 `preseed-mindmaps` 的「本地 Claude Code 當 LLM」路徑，**零 API 費用**（對比 Gemini Flash ~$0.3 / Claude Sonnet ~$3-5 每輪）

**執行方式**：
```bash
# 匯入完 → 切換到 preseed-mindmaps skill → 對剛匯入的 subject 跑預生
# Phase 1：蒐集考古題摘要 → /tmp/preseed_input_*.json
# Phase 2：Claude Code 本地分析 → /tmp/preseed_output_*.json（不呼叫外部 API）
# Phase 3：寫入 knowledge_nodes + 映射 questions.node_id
# Phase 4：驗證覆蓋率 + support_strength 分布
```

完整規範見 `.claude/skills/preseed-mindmaps/SKILL.md`，其中明定：
- 只動 `node_source='HISTORICAL_QA'`，不碰使用者上傳資源產生的 `RESOURCE_EXTRACTION`
- 重跑前備份 `knowledge_nodes_backup_YYYYMMDD`
- Production 前必須先在 local dev 驗證通過
- FK 處理（`questions.node_id` 非 CASCADE 要先 NULL-out）

**不使用此路徑的時機**：
- 使用者已上傳資源（走 `document_processing_service` → `UnifiedKnowledgeExtractionService`，會同時綜合 chunks + 考古題）
- 該科目沒有 `exam_subject_codes` 對應（空殼科目，需先補 catalog）

---

## 資料庫架構

```
questions ─── exam_id ──────→ exams           (使用者考試，AI 生成題)
    │
    └─── historical_exam_id → historical_exams (爬蟲匯入考古題)

CHECK: exam_id IS NOT NULL OR historical_exam_id IS NOT NULL
```

`historical_exams` 表欄位：
- `id` (uuid PK)
- `exam_code` (varchar 50) — 如 `114010`, `FIN114`
- `category_code` (varchar 100) — 如 `501`, `securities`
- `subject_code` (varchar 100) — 如 `0101`, `trust_regulations`
- `exam_name`, `category_name`, `subject_name` — 人類可讀名稱
- `source` — 資料來源
- `total_questions` — 題目數
- `year` — 民國年
- `tenant_id` — 多租戶隔離

---

## 檔案目錄結構

```
backend/data/historical_questions/
├── 114010/              # 高普考（6 位考試代碼）
│   ├── 501/             # 類科
│   │   ├── 0101.json    # 科目
│   │   └── 0102.json
│   └── 502/
├── 114080/
├── ipas/                # iPAS（類別名）
│   ├── big_data/
│   │   ├── 109_bda_beginner_sample_subject1.json
│   │   └── ...
│   └── information_security/
├── finance/             # 金融證照
│   ├── securities/
│   ├── trust/
│   └── ...
├── real_estate/         # 不動產
│   ├── broker/
│   └── ...
├── _pdf/                # 下載的原始 PDF（不匯入）
└── _catalog/            # 自動探測產出的目錄
```

---

## 快速指令

| 使用者說 | Claude 做 |
|----------|-----------|
| `爬取高普考 {年份}` | 掃描目錄 → 下載 PDF → 解析 → 匯入 |
| `爬取金融 {科目} {年份}` | 執行金融證照爬蟲 → 輸出標準 JSON |
| `分類 {JSON檔}` | 對已有題目進行 Bloom 分類 |
| `統計佔比 {科目}` | 輸出該科目歷年 Bloom 分佈趨勢 |
| `匯入題庫` | 執行 `import_exam_questions.py` |
| `正規化舊格式` | 執行 `normalize_json.py` |

---

## 現有題庫統計（2026-04-09）

| 來源 | exam_code | 題數 |
|------|-----------|------|
| 114 年高普考 | 114080 | 6,159 |
| 114 年初等考試 | 114010 | 1,833 |
| 金融證照 | FIN113-114 | 1,253 |
| iPAS | IPA109-114 | 576 |
| 不動產 | REA107-112 | 136 |
| **合計** | | **~9,957** |

---

## 注意事項

- **合法性**：僅爬取政府機關或公開考試機構的考古題，遵守 robots.txt
- **頻率限制**：每次請求間隔 1-2 秒，避免對目標網站造成負擔
- **PDF 解析**：使用 `pdfplumber`；考選部 PDF 使用 Unicode 選項標記（U+E18C~U+E18F → A~D）
- **Python 環境**：使用 `.venv/bin/python`（Python 3.13），不要用系統 python3
- **Bloom 分類 API**：使用 Gemini Flash 模型（成本低、速度快）
- **多租戶**：匯入時預設 tenant_id = `PUBLIC_B2C_TENANT_ID`（定義於 `app/core/config.py`）
