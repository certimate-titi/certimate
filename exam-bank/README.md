# exam-bank — TiTi 考題設計模組 v1.0.0

> **核心價值模組** — 獨立於前後端，由⭐考題設計人員負責管理。

## 模組職責

| 職責 | 說明 | 負責角色 |
|------|------|---------|
| 考古題爬取 | 從 SFI/考選部/iPAS 下載 PDF | 考題設計 |
| PDF 解析 | PDF → 標準 JSON（題目+選項+答案） | 考題設計 |
| Bloom 分類 | 自動標記 6 層認知層次 | 考題設計 |
| 題庫品質管理 | 答案正確率、選項完整性審核 | 考題設計 |
| 出題策略 | 抽題規則、難度比例、考點覆蓋 | 考題設計 |
| DB 匯入 | JSON → PostgreSQL questions 表 | 考題設計 + 後端研發 |

## 目錄結構

```
exam-bank/
├── README.md                    # 本檔案
├── VERSION                      # 模組版本（同步到 /VERSION.json）
├── crawlers/                    # 爬蟲腳本（按來源分）
├── parsers/                     # PDF → JSON 解析器
│   └── parse_exam_pdf.py        # 通用解析器（SFI/考選部/iPAS）
├── classifiers/                 # Bloom 分類器
├── strategies/                  # 出題策略規則
├── scripts/                     # 匯入/維護腳本
│   └── import_historical_questions.py
├── data/
│   ├── catalog.json             # 證照目錄索引（SSOT）
│   └── historical_questions/    # → symlink 到 backend/data/
└── docs/                        # 考題設計文件
```

## 版本管理

- 版本號記錄在 `/VERSION.json` 的 `exam_bank` 欄位
- 獨立於前端（frontend）和後端（backend）版本
- 變更遵循語意化版本：MAJOR.MINOR.PATCH

## 與後端的介面

| 介面 | 說明 |
|------|------|
| `backend/data/historical_questions/` | JSON 題庫檔案存放處 |
| `backend/alembic/versions/021_*` | 考科 seed（subject_categories + subjects） |
| `backend/alembic/versions/022_*` | bloom_category + historical_source 欄位 |
| `AiGenerationService._try_historical_questions()` | 考古題抽題邏輯 |

## 核心設計文件

| 文件 | 說明 |
|------|------|
| **[docs/exam-generation-spec.md](docs/exam-generation-spec.md)** | **出題引擎設計規格書** — ⭐考題設計人員最高準則 |

此規格書定義了 5 大設計原則、7 個已知問題、目標架構、和修正優先順序。
所有出題相關修改必須依據此文件執行。

## 當前統計 (v1.0.0)

| 指標 | 數值 |
|------|------|
| 證照類別 | 3（金融/不動產/iPAS） |
| 考科數 | 8 |
| 試卷數 | 45 |
| 題目數 | 2,786 |
| 有答案比例 | 94.8% |
| Bloom 覆蓋 | 6/6 層次 |
| 知識節點 | 32 |
