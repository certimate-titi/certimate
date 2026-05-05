# 考古題 PDF 轉換狀態檢查

時間：2026-05-05 03:02 (scheduled-task: exam-bank-pdf-check)

## 摘要

| 指標 | 數值 |
|------|------|
| PDF 總數（已掃描） | 45 |
| Manifest 條目數 | 45 |
| 已轉換 | 45 |
| 未轉換 | 0 |
| PDF 已變更（fingerprint 不符） | 0 |
| Manifest 中但檔案缺失 | 0 |

## 掃描範圍

- **掃描目錄**：`/Users/simon/certimate/project/backend/data/historical_questions/`
- **Manifest**：`/Users/simon/certimate/project/exam-bank/data/convert_manifest.json`
- **排除**：`_pdf/` 子目錄（切分後的小段）、`*_a.pdf`（答案檔）、檔名含 `answer` 者

## 結論

✅ 全數已轉換、無檔案變更、無待處理項目。本次無須執行 Gemini 轉換。

## 補充：品質警示（沿用上次紀錄）

下列 manifest 條目雖 status=ok，但 `quality_flag=review` 或 `questions=0`，建議下次人工抽檢（不在本巡檢任務範圍）：

- `finance/derivatives/futures_analyst_session01_questions.pdf` (review, with_answers=0)
- `ipas/big_data/108_bda_mid_practical.pdf` (review, questions=0)
- `ipas/information_security/114_is_mid_defense.pdf` (review, questions=0)
- `ipas/information_security/114_is_mid_planning.pdf` (review, questions=0)
- `real_estate/broker/111_broker_regulations_q.pdf` (review, questions=0)
- `real_estate/broker/111_civil_law_q.pdf` (review, questions=0)
- `real_estate/broker/111_valuation_q.pdf` (review, questions=0)
- `real_estate/broker/112_broker_regulations_q.pdf` (review, questions=0)
- `real_estate/broker/112_land_law_q.pdf` (review, questions=0)
- `real_estate/broker/112_valuation_q.pdf` (review, questions=0)

## 建議

無需動作。下次轉換指令備查：

```bash
cd exam-bank/parsers && python3 gemini_pdf_converter.py
```
