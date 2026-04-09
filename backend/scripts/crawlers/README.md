# 考選部高普考題庫爬蟲使用指南

## 概述

這套爬蟲工具用於自動蒐集台灣公務人員考試（高考三級、普考、初等考試）的考古題，提供給 CertiMate 平台使用。

**支援範圍**：
- 年份：最近 N 年（可自訂）
- 考試等級：高考三級、普考、初等考試
- 科目：所有選擇題科目
- 資料來源：考選部考畢試題查詢平臺 (https://wwwq.moex.gov.tw)

**技術特色**：
- ✓ 無需登入或複雜認證
- ✓ 直接下載原始 PDF 試題與答案
- ✓ 自動解析為結構化 JSON
- ✓ 支援大規模並行下載
- ✓ 容錯和重試機制

---

## 快速開始

### Step 1：自動生成 Catalog（可選）

如果要蒐集新年份或補充遺漏的科目：

```bash
cd backend

# 掃描 114 年（初等、高考、普考）
python3 scripts/crawlers/auto_catalog_generator.py --years 114

# 掃描多個年份
python3 scripts/crawlers/auto_catalog_generator.py --years 112 113 114

# 產生輸出：exam_catalog_complete.yaml
```

**耗時估算**：
- 單年份：~5-8 分鐘（並行掃描 ~1500 個 URL）
- 三年份：~15-20 分鐘

### Step 2：下載 PDF

使用現有或新生成的 Catalog 下載所有科目的試題和答案：

```bash
# 使用預設 catalog (exam_catalog.yaml)
python3 scripts/crawlers/moex_simple.py download

# 或指定自動生成的 catalog
python3 scripts/crawlers/moex_simple.py download --config exam_catalog_complete.yaml
```

**輸出位置**：`backend/data/historical_questions/_pdf/`

結構：
```
_pdf/
├── 114010/         # 114年初等考試
│   ├── 501/        # 一般行政類
│   │   ├── Q_0101.pdf  # 試題
│   │   ├── S_0101.pdf  # 答案
│   │   ├── Q_0102.pdf
│   │   └── S_0102.pdf
│   └── 502/        # 一般民政類
└── 114080/         # 114年高考+普考
    ├── 201/        # 高考一般行政
    ├── 401/        # 普考一般行政
    └── ...
```

### Step 3：解析 PDF 為 JSON

```bash
python3 scripts/crawlers/moex_simple.py parse
```

**輸出位置**：`backend/data/historical_questions/{年份}/{類科}/{科目}.json`

### Step 4：一次完成（推薦）

```bash
# 自動下載 + 解析
python3 scripts/crawlers/moex_simple.py all --config exam_catalog_complete.yaml
```

---

## 檔案說明

### `moex_simple.py` — 主爬蟲程式

**指令**：
```bash
usage: moex_simple.py [-h] [--config CONFIG] {download,parse,all}

  download    下載 PDF
  parse       解析 PDF → JSON
  all         下載 + 解析
```

**Options**：
- `--config YAML`: 指定 Catalog 檔案路徑（預設：`exam_catalog.yaml`）

**工作原理**：
1. `download` 命令：
   - 讀取 YAML Catalog
   - 對每個 exam_code/category_code/subject_code 組合
   - 下載 Q（試題）和 S（答案）PDF
   - 保存至 `_pdf/` 目錄

2. `parse` 命令：
   - 掃描 `_pdf/` 目錄中的所有 PDF
   - 使用 pdfplumber 提取文字
   - 正規表達式解析題目和選項
   - 匹配答案 PDF 以取得標準答案
   - 產生 JSON（與 CertiMate 資料庫 schema 相容）

### `auto_catalog_generator.py` — Catalog 自動生成器

**指令**：
```bash
python3 auto_catalog_generator.py \
  --years 112 113 114 \
  --output exam_catalog_complete.yaml \
  --workers 8 \
  --delay 0.3
```

**Options**：
- `--years`: 掃描的民國年份（預設：112 113 114）
- `--output`: 輸出 YAML 檔案名稱
- `--workers`: 並行掃描的執行緒數（預設：8，建議 4-10）
- `--delay`: 請求間延遲秒數（預設：0.3，禮貌設定）

**掃描邏輯**：
1. 對每個年份和考試等級（初等、高考、普考）
2. 掃描已知的類科代碼範圍：
   - 初等：501-516（16 個）
   - 普考：401-455（55 個）
   - 高考：201-300（100 個）
3. 對每個類科，嘗試常見的科目代碼（0101, 0102, 0401 等）
4. 檢查答案 PDF 是否存在 → 存在 = 有效（選擇題）
5. 產生完整的 YAML Catalog

### `exam_catalog.yaml` — 考試科目配置檔

**格式**：
```yaml
"114010":                # 考試代碼（114年初等考試）
  "501":                 # 類科代碼（一般行政）
    - "0101"             # 科目代碼（國文）
    - "0102"             # 科目代碼（公民與英文）
    - "0501"             # 科目代碼（管理概要）
    - "0502"             # 科目代碼（法律常識）
  
  "502":                 # 另一個類科（一般民政）
    - "0101"
    - "0102"
    - ...

"114080":                # 114年高考三級及普通考試
  "201":                 # 高考一般行政（201-300 = 高考）
    - "0101"
    - "0401"
    - "0301"
    ...
  
  "401":                 # 普考一般行政（401-455 = 普考）
    - "0102"
    - "0402"
    ...
```

**編輯方式**：
- 手動編輯：在 YAML 中直接新增/刪除考試、類科、科目
- 自動生成：執行 `auto_catalog_generator.py` 覆蓋整個檔案

---

## JSON 輸出格式

**檔案結構**：
```
114010/           # 考試年份+等級
├── 501/          # 類科
│   ├── 0101.json # 科目 JSON
│   ├── 0102.json
│   └── ...
└── 502/
    └── ...
```

**JSON 內容**：
```json
{
  "import_meta": {
    "source": "考選部考畢試題查詢平臺",
    "exam_code": "114010",
    "category_code": "501",
    "subject_code": "0101",
    "total_questions": 35,
    "questions_with_answer": 35
  },
  "questions": [
    {
      "question_number": 1,
      "content": "下列文句「」中的成語用法，何者正確？",
      "type": "single_choice",
      "option_a": "當一個人做事「行不由徑」，信用和形象都已被打折扣",
      "option_b": "她講話總是「拾人牙慧」，充滿個人獨特的想法與見解",
      "option_c": "上司若為人正直，行事端正，相信下屬也會「群起效尤」",
      "option_d": "工作要先計畫周全再開始執行，才能收「事半功倍」之效",
      "correct_answer": "D",
      "explanation": "",
      "bloom_category": null
    },
    ...
  ]
}
```

**欄位說明**：
- `question_number`: 題號（1-N）
- `content`: 題幹/提問
- `type`: 題目類型（預設：single_choice）
- `option_a/b/c/d`: 四個選項文字
- `correct_answer`: 標準答案（A/B/C/D）
- `explanation`: 解說（目前為空，可後續補充）
- `bloom_category`: Bloom 認知層次（null = 待分類）

---

## 常見問題

### Q1：為什麼有些 PDF 無法解析？
**A**：可能原因：
- 申論題科目沒有答案 PDF → skip
- PDF 格式變化 → 正規表達式需更新
- 文字提取失敗 → 可嘗試其他 PDF 庫

### Q2：能否只下載特定類科？
**A**：可以。編輯 YAML，只保留目標考試/類科/科目，其他刪除。

### Q3：下載失敗了怎麼辦？
**A**：
1. 檢查網路連線
2. 確認 URL 正確（可手動測試：`curl "https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx?t=S&code=114010&c=501&s=0101&q=1" -k`）
3. 重新執行 download → 已存在的 PDF 會自動跳過

### Q4：如何支援 Bloom 認知層次分類？
**A**：
1. 呼叫 Gemini/Claude API
2. 將 `bloom_category` 從 `null` 改為 `remember/understand/apply/analyze/evaluate/create`
3. 可另寫腳本在下載後批量分類

### Q5：可否自訂題目正規表達式？
**A**：編輯 `moex_simple.py` 的 `parse_mc_questions()` 函式。需要根據 PDF 格式調整。

---

## 技術細節

### HTTP 請求

**下載 URL 格式**：
```
https://wwwq.moex.gov.tw/exam/wHandExamQandA_File.ashx
  ?t=Q|S|A           # Q=試題, S=答案, A=全部答案
  &code=114010       # 考試代碼
  &c=501             # 類科代碼
  &s=0101            # 科目代碼
  &q=1               # 題號（固定為 1）
```

**Response**：
- 成功：HTTP 200，Content-Type: application/pdf，大小 > 1000 bytes
- 失敗：HTTP 404 或空檔案

### 並行處理

**ThreadPoolExecutor**：
- 預設 8 個執行緒
- 可調整 `--workers` 參數
- 建議：4-10（超過 10 可能被考選部伺服器限制）

### 禮貌考量

**延遲設定**：
- 預設 0.4 秒/請求
- 可調整 `--delay` 參數
- 確保不對考選部伺服器造成負擔

---

## 集成到 CertiMate

### 1. 匯入 JSON 到資料庫

```python
# backend/app/scripts/import_exam_questions.py
from pathlib import Path
import json

def import_from_json(json_dir: Path):
    """掃描 JSON 檔案並匯入資料庫"""
    for json_file in json_dir.rglob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
        
        # TODO: 實作 insert_questions() 
        insert_questions(
            exam_code=data["import_meta"]["exam_code"],
            category=data["import_meta"]["category_name"],
            subject=data["import_meta"]["subject_name"],
            questions=data["questions"]
        )
```

### 2. 後續步驟

- [ ] 將 JSON 匯入 `questions` 表
- [ ] 關聯到 `exams`、`subjects` 表
- [ ] 觸發 Bloom 分類工作（Celery）
- [ ] 生成題庫統計報表

---

## 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| 1.0 | 2026-04-08 | 初版：下載 + 解析 + 自動 Catalog 生成 |

---

## 聯絡與回饋

如有問題或改進建議，請提交 Issue 或聯繫開發團隊。

Happy studying! 📚
