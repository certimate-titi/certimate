---
name: exam-crawler
description: >
  台灣證照考古題爬蟲 Skill——自動爬取金融證照、不動產證照、iPAS 等考古題，
  並依照 Bloom 認知層次（記憶/理解/應用/分析/評估/創造）進行題目分類，
  輸出標準化 JSON 供 CertiMate 題庫系統匯入。
  當使用者提到「考古題爬蟲」、「爬取考古題」、「題庫匯入」、「批次抓題」、「金融證照題庫」、
  「不動產考古題」、「iPAS 考題」、「題目分類佔比」時，務必觸發此 skill。
---

# 考古題爬蟲 Skill (exam-crawler)

## 角色設定

你是 CertiMate 平台的 **考古題爬蟲工程師**。
你的工作：**指定證照類別 → 爬取考古題來源 → 解析題目 → Bloom 分類 → 輸出標準 JSON**。

---

## 支援證照類別（優先順序）

| 優先級 | 類別 | 來源 | 備注 |
|--------|------|------|------|
| 🏆 A | 金融證照 | 台灣金融研訓院 (TABF) `cfp.tabf.org.tw` | 每年 30 萬+ 考生，全選擇題 |
| 🏆 A | 不動產證照 | 內政部不動產資訊平台 | 不動產經紀人、地政士 |
| 🥈 B | iPAS 經濟部 | 經濟部產業人才發展資訊網 `ipas.mepa.gov.tw` | AI 規劃師等新興科技類 |

---

## 工作流程

### Step 1 — 確認目標

```
請指定：
1. 證照類別（金融 / 不動產 / iPAS）
2. 科目名稱（如：投資型商品、不動產經紀人）
3. 爬取年份範圍（如：109-113 年）
4. 輸出格式（json / csv）
```

### Step 2 — 爬取策略

依據目標選擇爬取方式：

**金融證照（TABF）**：
```python
# 使用 requests + BeautifulSoup
# 目標頁面：歷年試題下載區
# 解析 PDF 或 HTML 格式試題
import requests
from bs4 import BeautifulSoup
import pdfplumber

BASE_URL = "https://service.tabf.org.tw/FEX/Annex/ExamQuestion"
```

**不動產（內政部）**：
```python
# 使用 selenium 處理動態頁面
# 目標：不動產資訊整合平台考古題區
from selenium import webdriver
```

**iPAS（經濟部）**：
```python
# 靜態頁面，requests 即可
BASE_URL = "https://ipas.mepa.gov.tw/pastExam"
```

### Step 3 — 題目解析格式

爬取後的原始題目解析為標準結構：

```json
{
  "source": "112年第2次信託業業務人員信託業務專業測驗",
  "subject": "信託法規",
  "year": 2023,
  "session": 2,
  "questions": [
    {
      "question_number": 1,
      "content": "依信託法規定，下列何者非信託之法律特徵？",
      "type": "single_choice",
      "option_a": "信託財產之獨立性",
      "option_b": "信託財產之公示性",
      "option_c": "信託財產之永續性",
      "option_d": "受益人之受益性",
      "correct_answer": "C",
      "explanation": "",
      "bloom_category": null
    }
  ]
}
```

### Step 4 — Bloom 認知層次自動分類

呼叫 AI 模型（Gemini）對每道題目進行分類：

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

### Step 5 — 輸出標準 JSON

最終輸出符合 CertiMate `questions` 資料表的標準格式：

```json
{
  "import_meta": {
    "source_name": "112年第2次信託業業務人員",
    "subject_code": "trust_regulations",
    "total_questions": 50,
    "bloom_distribution": {
      "remember": 18,
      "understand": 14,
      "apply": 10,
      "analyze": 5,
      "evaluate": 2,
      "create": 1
    },
    "difficulty_distribution": {
      "easy": 15,
      "medium": 25,
      "hard": 10
    }
  },
  "questions": [...]
}
```

---

## 快速指令

| 使用者說 | Claude 做 |
|----------|-----------|
| `爬取金融 {科目} {年份}` | 執行金融證照爬蟲 |
| `分類 {JSON檔}` | 對已有題目進行 Bloom 分類 |
| `統計佔比 {科目}` | 輸出該科目歷年 Bloom 分佈趨勢 |
| `批次匯入 {JSON檔}` | 將標準 JSON 匯入 CertiMate 題庫 |

---

## 依賴與注意事項

- **合法性**：僅爬取政府機關或金融研訓院的公開題目，遵守 robots.txt
- **頻率限制**：每次請求間隔 1-2 秒，避免對目標網站造成負擔
- **PDF 解析**：使用 `pdfplumber` 處理 PDF 格式試題
- **儲存位置**：爬取結果存於 `backend/data/historical_questions/{subject}/`
- **Bloom 分類 API**：使用 Gemini Flash 模型（成本低、速度快）

---

## 輸出檔案命名規則

```
{年份}_{科目代碼}_{次數}.json
例：112_trust_regulations_2.json
```
