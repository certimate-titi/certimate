# 考古題 PDF 轉換狀態檢查
時間：2026-04-13 00:00:00（自動排程）
已轉換：45 份
未轉換：410 份
PDF 已變更：0 份

## 摘要

manifest 中所有 45 份已轉換 PDF 的 SHA256 fingerprint 均與磁碟吻合（無變更）。
新增 410 份未轉換 PDF，全部來自 `_pdf/` 目錄（高普考爬蟲產出）。

## 已轉換 PDF（45 份，狀態 OK）

| 類別 | 數量 |
|------|------|
| finance/anti_money_laundering | 4 |
| finance/derivatives | 6 |
| finance/financial_planning | 4 |
| finance/securities | 8 |
| ipas/ai_planner | 5 |
| ipas/big_data | 5 |
| ipas/information_security | 4 |
| real_estate/broker | 9 |
| **合計** | **45** |

## 未處理清單（410 份）

所有未轉換 PDF 均位於 `backend/data/historical_questions/_pdf/` 目錄，為高普考爬蟲產出。

| 考試場次 | 科目數 | 題目 PDF 數 | 預估大小 |
|---------|-------|-----------|---------|
| 114010（114年第1次） | 16 | 60 | ~24 MB |
| 114080（114年第8次） | 149 | 350 | ~85 MB |
| **合計** | **165** | **410** | **~109 MB** |

> 每份 PDF 平均 267 KB，均為個別科目題組（每份約 20–80 題）。

### 未轉換 PDF 路徑（前 30 筆）

```
_pdf/114010/501/Q_0101.pdf
_pdf/114010/501/Q_0102.pdf
_pdf/114010/501/Q_0202.pdf
_pdf/114010/501/Q_0302.pdf
_pdf/114010/501/Q_0501.pdf
_pdf/114010/501/Q_0502.pdf
_pdf/114010/502/Q_0101.pdf
_pdf/114010/502/Q_0102.pdf
_pdf/114010/502/Q_0202.pdf
_pdf/114010/502/Q_0303.pdf
_pdf/114010/502/Q_0503.pdf
_pdf/114010/502/Q_0504.pdf
_pdf/114010/503/Q_0101.pdf
_pdf/114010/503/Q_0102.pdf
_pdf/114010/503/Q_0202.pdf
_pdf/114010/503/Q_0203.pdf
... 共 410 份（詳見待決議文件）
```

## 預估成本

| 項目 | 數值 |
|------|------|
| 未轉換 PDF 數 | 410 份 |
| 平均大小 | 267 KB / 份 |
| 引擎 | Gemini 2.5 Flash |
| 每份估算 | ~$0.05 USD |
| **總估算** | **~$20 USD** |

## 建議

執行以下指令進行批次轉換（需要 GEMINI_API_KEY）：

```bash
cd exam-bank/parsers && python3 gemini_pdf_converter.py
```

> **注意**：_pdf/ 目錄為高普考爬蟲產出，其路徑結構（`考試代碼/科目代碼/Q_xxxx.pdf`）可能需要確認轉換器是否支援此路徑格式，建議先以 1–2 份測試後再批次執行。

---
_由 exam-bank-pdf-check 自動排程產出_
