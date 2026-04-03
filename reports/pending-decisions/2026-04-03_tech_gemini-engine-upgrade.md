---
type: decision-request
priority: medium
from: 考題設計人員
date: 2026-04-03
status: approved
okr: O3-KR1
---

## 決議請求：PDF 轉換引擎正式從 Claude Sonnet 切換至 Gemini Flash

### 背景

已完成 Gemini 2.5 Flash PDF 轉換器的開發與測試。需要正式確認引擎切換。

### 新舊引擎對比

| 指標 | 舊引擎 (Claude Sonnet) | 新引擎 (Gemini 2.5 Flash) |
|------|----------------------|--------------------------|
| 轉換方式 | pdfplumber 文字提取 → 分批 LLM | Gemini 原生 PDF 上傳（單次呼叫） |
| 速度（80 題 PDF） | 15-30 秒 | 38-55 秒（含 4 層驗證） |
| 成本/份 | ~$0.06 | ~$0.005 |
| 數學公式 | 文字提取丟失，LLM 猜測還原 | 直接讀取 PDF 原始排版 |
| 品質驗證 | 無 | 4 層自動驗證 |
| 內容偵測 | 無（假設全是考題） | Stage 0 自動分類 |
| Manifest | size+mtime | SHA256 fingerprint |

### 測試結果

| 測試 PDF | 題數 | 驗證結果 | 耗時 |
|----------|------|----------|------|
| 防制洗錢（SFI） | 80 題 | L1 ✅ L3 ✅ L4 ✅ | 55 秒 |
| 期貨業務員（SFI） | 100 題 | L1 ✅ L3 ✅ L4 ✅ | 55 秒 |
| 數學公式驗證（iPAS ML） | 50 題 | $R^2$, $\lambda$, $O(n^2)$ 正確 | 48 秒 |

### 注意事項

- Gemini 2.5 Flash 的「思考模式」已關閉（`thinking_budget=0`），不影響數學公式品質
- 舊轉換器 `llm_pdf_converter.py` 保留作為 fallback（Gemini API 故障時）
- 排程 `exam-bank-pdf-check` 和 `weekly-exam-crawl` 的報告產出位置需更新為 `reports/` 目錄

### CEO 建議

建議批准切換。新引擎在成本、品質驗證上全面優於舊引擎。速度雖然總體相近（因為含驗證），但品質保障大幅提升。

### 董事會決議

> 2026-04-03 董事會批准：正式切換至 Gemini 2.5 Flash 引擎
