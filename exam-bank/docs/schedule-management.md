# TiTi 排程工作管理總覽

> **版本**：v2.0 | 2026-04-03
> **負責角色**：運營工程師 + CEO 統整
> **審核**：董事會
> **目標對齊**：O3-KR1（LLM 成本控制）、O1-KR3（信度覆蓋率）

---

## 一、雙軌 Pipeline 架構

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TiTi PDF 處理雙軌架構                             │
│                                                                     │
│  Pipeline A — 題庫維運（批次，低頻，需人工批准）                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 每週五 02:00 │→ │ 每日 03:00   │→ │ 每月第一週一  │              │
│  │ 考古題爬取   │  │ PDF 轉換檢查 │  │ 文件審查     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         ▼                 ▼                 ▼                       │
│    crawl-reports/    conversion-reports/  doc-review-reports/        │
│         │                 │                                         │
│  ─ ─ ─ ┼─ ─ ─ ─ ─ ─ ─ ─┼─ ─  人工確認閘門  ─ ─ ─ ─ ─ ─ ─       │
│         ▼                 ▼                                         │
│    PDF 下載          Gemini Flash 轉換                               │
│   （董事會批准）      （董事會批准）                                   │
│                                                                     │
│─────────────────────────────────────────────────────────────────────│
│                                                                     │
│  Pipeline B — 用戶上傳（即時，高頻，全自動）                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 用戶上傳 PDF │→ │ Stage 0 偵測 │→ │ Gemini Flash │              │
│  │              │  │ 內容分類     │  │ 轉換 + 驗證  │              │
│  └──────────────┘  └──────────────┘  └──────┬───────┘              │
│                                             ▼                       │
│                                     自動匯入 DB（無需人工）           │
│                                     方案限制 = 成本控制               │
└─────────────────────────────────────────────────────────────────────┘
```

### Pipeline A vs B 差異

| 項目 | Pipeline A（題庫維運） | Pipeline B（用戶上傳） |
|------|----------------------|----------------------|
| 觸發方式 | 排程 cron | 用戶上傳即時觸發 |
| 人工批准 | 需要（董事會決議） | 不需要（全自動） |
| 轉換引擎 | Gemini 2.5 Flash | Gemini 2.5 Flash |
| 品質驗證 | 4 層完整驗證 | 4 層完整驗證 |
| 成本控制 | manifest 防重複 + 人工閘門 | 方案上傳上限 |
| 報告產出 | `reports/` 目錄 | 用戶端顯示結果 |
| 信度標示 | 🟢 考古題 | 🟡 用戶上傳 |

---

## 二、報告產出中心

所有排程報告集中產出至 `reports/` 目錄，供董事會一站式審查。

```
reports/
  ├── README.md                  ← 報告中心索引
  ├── pending-decisions/         ← 待董事會決議的事項
  ├── crawl-reports/             ← 每週五 考古題爬取報告
  ├── conversion-reports/        ← 每日 PDF 轉換狀態報告
  ├── doc-review-reports/        ← 每月 文件審查報告
  └── weekly-summary/            ← 每週一 CEO 週報匯總
```

---

## 三、排程工作詳細說明

### 排程 1：每日 PDF 轉換檢查

| 項目 | 內容 |
|------|------|
| **排程 ID** | `exam-bank-pdf-check` |
| **頻率** | 每日凌晨 03:00（本地時間） |
| **負責角色** | ⭐ 考題設計人員（審查）+ 運營工程師（執行） |
| **目標對齊** | O1-KR3 信度標示覆蓋率 100% |
| **成本** | $0（僅檔案比對，無 LLM 呼叫） |
| **報告位置** | `reports/conversion-reports/conversion-status-YYYY-MM-DD.md` |
| **待決議** | 未轉換 > 5 份時 → `reports/pending-decisions/` |

#### 工作內容

1. 讀取 `exam-bank/data/convert_manifest.json`
2. 掃描 `backend/data/historical_questions/` 所有 PDF（排除 answer 檔）
3. 比對：未轉換 / fingerprint 變更
4. 產出報告至 `reports/conversion-reports/`
5. 超過 5 份未轉換 → 建立待決議文件

#### 後續人工動作

- 董事會審查待決議 → 批准執行 `gemini_pdf_converter.py`
- 預估成本：~$0.005/份（Gemini Flash）
- 轉換含 4 層品質驗證，自動匯入

---

### 排程 2：每週考古題網站爬取

| 項目 | 內容 |
|------|------|
| **排程 ID** | `weekly-exam-crawl` |
| **頻率** | 每週五凌晨 02:00（本地時間） |
| **負責角色** | ⭐ 考題設計人員（審查）+ 運營工程師（執行） |
| **目標對齊** | O1-KR1 AI 生成答案正確率 ≥ 95%（題庫豐富度） |
| **成本** | $0（僅網頁爬取） |
| **報告位置** | `reports/crawl-reports/crawl-report-YYYY-MM-DD.md` |
| **待決議** | 發現新考古題 → `reports/pending-decisions/` |

#### 爬取來源

| 來源 | 網站 | 涵蓋科目 |
|------|------|----------|
| 證基會 SFI | examweb.sfi.org.tw | 證券、期貨、投信投顧、防制洗錢 |
| iPAS | ipas.ceec.org.tw | AI 應用規劃師、巨量資料、資安 |
| 考選部 | wwwc.moex.gov.tw | 不動產經紀人、地政士、估價師 |

#### 後續人工動作

- 董事會審查待決議 → 批准下載 PDF
- 下載後次日 03:00 自動被 PDF 轉換檢查偵測

---

### 排程 3：每月文件審查

| 項目 | 內容 |
|------|------|
| **排程 ID** | `monthly-doc-review` |
| **頻率** | 每月第一個週一 09:00 |
| **負責角色** | CEO + 各文件負責角色 |
| **目標對齊** | O3-KR1 成本控制（文件準確 = 決策準確） |
| **成本** | $0（檔案比對 + 提醒） |
| **報告位置** | `reports/doc-review-reports/doc-review-YYYY-MM.md` |
| **待決議** | 有過期文件 → `reports/pending-decisions/` |

#### 審查清單

| 文件 | 位置 | 負責角色 | 審查重點 |
|------|------|----------|----------|
| 出題引擎規格書 | `exam-bank/docs/exam-generation-spec.md` | ⭐ 考題設計 | 4 層 Pipeline 是否與實作一致 |
| 品質保障規格書 | `exam-bank/docs/question-quality-assurance.md` | ⭐ 考題設計 | 品質閘門規則是否更新 |
| PDF→MD 轉換規格 | `exam-bank/docs/pdf-to-markdown-spec.md` | ⭐ 考題設計 | Gemini Flash Prompt、成本 |
| AI 教練規格書 | `exam-bank/docs/ai-coach-spec.md` | Prompt 工程師 | 蘇格拉底策略 |
| 上傳→出題 Pipeline | `exam-bank/docs/upload-to-question-pipeline.md` | 後端研發 | Pipeline B 是否與 API 一致 |
| DBML Schema | `project/specs/entity/erm.dbml` | 後端研發 | 是否與 migration 同步 |
| Feature 規格 | `project/features/*.feature` | 產品經理 | 是否與實作對齊 |
| 排程管理總覽 | `exam-bank/docs/schedule-management.md` | 運營工程師 | 排程運作、頻率調整 |

---

## 四、排程依賴關係

```
每週五 02:00                    每日 03:00                每月第一週一
考古題爬取                      PDF 轉換檢查              文件審查
    │                               │                        │
    │ 發現新考古題                    │ 發現未轉換 PDF          │ 發現過期文件
    ▼                               ▼                        ▼
┌──────────┐  下載後自動進入  ┌──────────────┐         ┌──────────┐
│ 董事會    │ ──────────────→ │ Gemini Flash │         │ 指派更新  │
│ 批准下載  │                 │ 轉換+4層驗證  │         │ 負責角色  │
└──────────┘                 │（董事會批准） │         └──────────┘
                             └──────┬───────┘
                                    │
                                    ▼
                             ┌──────────────┐
                             │ 自動匯入 DB  │
                             │ + Bloom 分類  │
                             └──────────────┘
```

| 上游排程 | 下游動作 | 觸發方式 |
|----------|----------|----------|
| 考古題爬取 → | PDF 下載 | 董事會批准 |
| PDF 下載完成 → | PDF 轉換檢查偵測 | 次日自動 |
| PDF 轉換檢查 → | Gemini Flash 轉換 | 董事會批准 |
| 轉換完成 → | 4 層品質驗證 + DB 匯入 | 自動 |

---

## 五、成本控制

### 排程本身成本

| 排程 | 頻率 | 每次成本 | 月成本 |
|------|------|----------|--------|
| PDF 轉換檢查 | 30 次/月 | $0 | **$0** |
| 考古題爬取 | 4 次/月 | $0 | **$0** |
| 文件審查 | 1 次/月 | $0 | **$0** |
| **小計** | | | **$0/月** |

### Pipeline A 觸發成本（董事會批准後）

| 動作 | 引擎 | 單次成本 | 說明 |
|------|------|----------|------|
| PDF 轉換 | Gemini 2.5 Flash | ~$0.005/份 | 含 4 層驗證 |
| Cross-LLM 驗證 | Gemini Flash | ~$0.003/份 | Layer 3 抽樣覆核 |
| **單份總成本** | | **~$0.009** | 舊版 $0.06 → 降低 85% |

### Pipeline B 成本控制（方案上傳上限）

| 方案 | 每月上傳上限 | 最大月成本/用戶 |
|------|-------------|----------------|
| FREE | 3 份 | $0.027 |
| PRO_199 | 20 份 | $0.18 |
| PRO_PLUS_399 | 50 份 | $0.45 |
| ULTRA_1599 | 無限 | 監控告警 |

### 成本安全閥

- Pipeline A：`convert_manifest.json` 防重複 + 董事會批准閘門
- Pipeline B：方案上傳上限 + SHA256 fingerprint 防重複
- 兩條 Pipeline 共用：Gemini Flash（$0.15/$0.60 per MTok，比 Claude Sonnet 便宜 20x）

---

## 六、監控與異常處理

### 正常運作指標

| 指標 | 預期值 | 異常閾值 |
|------|--------|----------|
| PDF 轉換檢查執行 | 每日 1 次 | 連續 3 天未執行 |
| 考古題爬取執行 | 每週 1 次 | 連續 2 週未執行 |
| 未轉換 PDF 積壓 | ≤ 5 份 | > 10 份 → 待決議 |
| 爬取報告產出 | 每週 1 份 | 連續 2 週無報告 |
| 待決議積壓 | ≤ 3 件 | > 5 件 → CEO 上報 |

### 異常處理流程

| 異常 | 影響 | 處理方式 |
|------|------|----------|
| 排程未執行 | 新考古題遺漏 | 檢查 Claude Code 是否在運行，手動觸發 |
| 爬取網站不可用 | 無法偵測新題 | 記錄錯誤，不中斷其他來源，下週重試 |
| Gemini API 故障 | 轉換中斷 | fallback 至 `llm_pdf_converter.py`（Claude Sonnet） |
| manifest 損壞 | 可能重複轉換 | 從 `data/markdown/` 實際檔案重建 manifest |
| 文件與實作不一致 | 決策依據錯誤 | 月度審查時修正，嚴重時 CEO 緊急上報 |

---

## 七、角色職責矩陣 (RACI)

| 排程工作 | ⭐考題設計 | 後端研發 | 運營工程師 | CEO | 董事會 |
|----------|-----------|----------|-----------|-----|--------|
| PDF 轉換檢查 | C | I | R | A | I |
| 考古題爬取 | C | I | R | A | I |
| 批准批次轉換 | C | I | R | A | **決策** |
| 批准 PDF 下載 | C | I | R | A | **決策** |
| Pipeline B（用戶上傳） | C | R | C | A | I |
| 文件定期審查 | R（考題） | R（API） | R（排程） | A | I |
| 排程新增/修改 | C | C | R | A | I |

> R = Responsible、A = Accountable、C = Consulted、I = Informed

---

## 八、文件索引

### 規格文件

| # | 文件 | 位置 | 版本 | 說明 |
|---|------|------|------|------|
| 1 | 出題引擎規格書 | `exam-bank/docs/exam-generation-spec.md` | v2.0 | 4 層混合式出題 Pipeline |
| 2 | 品質保障規格書 | `exam-bank/docs/question-quality-assurance.md` | v3.0 | 4 層品質框架 + Cross-LLM 驗證 |
| 3 | PDF→MD 轉換規格 | `exam-bank/docs/pdf-to-markdown-spec.md` | **v2.0** | Gemini Flash + 7 種 ContentType |
| 4 | AI 教練規格書 | `exam-bank/docs/ai-coach-spec.md` | v2.0 | 蘇格拉底教學法 + 信心象限 |
| 5 | 上傳→出題 Pipeline | `exam-bank/docs/upload-to-question-pipeline.md` | **v2.0** | 雙軌 Pipeline + ContentType 分流 |
| 6 | 排程管理總覽 | `exam-bank/docs/schedule-management.md` | **v2.0** | 雙軌 Pipeline + 報告中心 |
| 7 | 內容類型規格書 | `exam-bank/docs/content-type-spec.md` | v1.0 | 7 種 ContentType 定義 + DB Schema |

### 排程檔案

| # | 排程 | 位置 | 頻率 |
|---|------|------|------|
| 1 | PDF 轉換檢查 | `~/.claude/scheduled-tasks/exam-bank-pdf-check/` | 每日 03:00 |
| 2 | 考古題爬取 | `~/.claude/scheduled-tasks/weekly-exam-crawl/` | 每週五 02:00 |
| 3 | 文件審查 | `~/.claude/scheduled-tasks/monthly-doc-review/` | 每月第一週一 09:00 |

### 執行腳本

| # | 腳本 | 位置 | 用途 |
|---|------|------|------|
| 1 | **Gemini Flash 轉換器** | `exam-bank/parsers/gemini_pdf_converter.py` | PDF → MD（主引擎） |
| 2 | Claude Sonnet 轉換器 | `exam-bank/parsers/llm_pdf_converter.py` | PDF → MD（fallback） |
| 3 | 舊 regex 解析器 | `exam-bank/parsers/parse_exam_pdf.py` | PDF → JSON（已棄用） |
| 4 | 題庫匯入腳本 | `exam-bank/scripts/import_historical_questions.py` | JSON → DB 匯入 |
| 5 | 出題規劃器 | `exam-bank/strategies/question_planner.py` | 4 層 Pipeline 邏輯 |
| 6 | 品質驗證器 | `exam-bank/strategies/question_validator.py` | Layer 1 閘門 + Cross-LLM |

### 報告目錄

| # | 目錄 | 用途 |
|---|------|------|
| 1 | `reports/pending-decisions/` | 待董事會決議事項 |
| 2 | `reports/crawl-reports/` | 每週爬取報告 |
| 3 | `reports/conversion-reports/` | 每日轉換狀態報告 |
| 4 | `reports/doc-review-reports/` | 每月文件審查報告 |
| 5 | `reports/weekly-summary/` | CEO 週報 |

---

## 版本紀錄

| 版本 | 日期 | 修改內容 | 負責人 |
|------|------|----------|--------|
| v1.0 | 2026-04-03 | 初版建立 | 運營工程師 + CEO |
| v2.0 | 2026-04-03 | 雙軌 Pipeline、報告中心、Gemini Flash 引擎、排程報告路徑更新 | 運營工程師 + CEO |
