# CertiMate 考古題資料庫

## 現況統計（2026-04-02）

| 類別 | 試卷 | 題目 | 有答案 | DB 狀態 |
|------|------|------|--------|---------|
| 金融證照 | 22 | 2,067 | 100% | Migration 021 已寫入 |
| 不動產證照 | 9 | 143 | 0% | Migration 021 已寫入 |
| iPAS 產業人才鑑定 | 14 | 576 | 100% | Migration 021 已寫入 |
| **合計** | **45** | **2,786** | **95%** | **3 categories + 14 subjects** |

## 目錄結構

```
historical_questions/
├── catalog.json                    # 證照目錄索引（含 DB UUID 映射）
├── parse_exam_pdf.py               # PDF → JSON 解析器
├── finance/                        # 金融證照（Priority A）
│   ├── securities/                 # 證券商業務員（16 PDF + 4 JSON）
│   ├── derivatives/                # 期貨商業務員（12 PDF + 6 JSON）
│   ├── anti_money_laundering/      # 防制洗錢（8 PDF + 4 JSON）
│   ├── financial_planning/         # 投信投顧（8 PDF + 4 JSON）
│   ├── trust/                      # 信託（待爬取）
│   └── insurance/                  # 保險（待爬取）
├── real_estate/                    # 不動產證照（Priority A）
│   ├── broker/                     # 經紀人（10 PDF + 9 JSON）
│   ├── land_agent/                 # 地政士（待爬取）
│   └── appraiser/                  # 估價師（待爬取）
└── ipas/                           # iPAS（Priority B）
    ├── ai_planner/                 # AI 規劃師（5 PDF + 5 JSON）
    ├── big_data/                   # 巨量資料（5 PDF + 5 JSON）
    ├── information_security/       # 資安工程師（4 PDF + 4 JSON）
    ├── iot/                        # 物聯網（待爬取）
    └── blockchain/                 # 區塊鏈（待爬取）
```

## 與 DB 的對應

### Alembic Migration 021

Migration 021 將以下資料寫入 `subject_categories` 和 `subjects` 表：

- **3 個 subject_categories**：金融證照 / 不動產證照 / iPAS 產業人才鑑定
- **14 個 subjects**：每個使用固定 UUID，便於跨環境一致

### UUID 映射

`catalog.json` 中的 `subject_code_to_db_mapping` 記錄了每個科目代碼對應的 DB UUID。
匯入題目時，使用此映射關聯 `questions.historical_source` 到正確的 `subjects.id`。

### Admin Seed API

`POST /api/v1/admin/seed-subjects`（無 body）會自動匯入預設 6 類 26 科考科，
包含考古題爬蟲的 14 科 + 原有的 IT/語言/醫療。

## JSON 格式

每個 `.json` 檔案遵循標準格式：
- `import_meta` — 來源、科目、題數、Bloom 分佈統計
- `questions[]` — 題目陣列，每題含 `bloom_category` 分類

## Bloom 認知層次分佈

```
remember     76.1%  ██████████████████████████████████████
apply         8.6%  ████
analyze       7.2%  ███
understand    3.0%  █
create        2.7%  █
evaluate      2.5%  █
```
