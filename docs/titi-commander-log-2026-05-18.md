# TiTi Commander 排程巡檢紀錄 — 2026-05-18 20:06 UTC

> **觸發方式**：Cowork 排程任務（check-todo）
> **執行模式**：自動巡檢（無人值守）

---

## 1. ToDoList 掃描結果

掃描 `docs/ToDoList.md`，識別出 **11 項未完成待辦**：

### P1（高優先）
| # | 項目 | 狀態 |
|---|------|------|
| 1 | Feature 10 L577-586 Scenario 誤導（CSV 匯入描述為即將推出） | **本次修復** |
| 2 | `/pricing` → ECPay 訂閱付款整合仍為 TODO | 待開發（需金流整合，不適合自動處理） |

### P2（中優先）
| # | 項目 | 狀態 |
|---|------|------|
| 3 | `/exam/workspace` EPIC-035 AI inference 判斷按鈕未整合 | 待開發 |
| 4 | `/edu-console` 派發模擬考卷快速卡片為 alert() stub | 待開發 |
| 5 | `/edu-console` 匯出詳細報告按鈕為 alert() stub | 待開發 |
| 6 | `/edu-console/student/[id]` 匯出報告與複習排程為 alert() stub | 待開發 |
| 7 | `/exam/results` Feature 06 Certi 情感表情 UI 與 spec 有落差 | 待開發 |

### P3（低優先）
| # | 項目 | 狀態 |
|---|------|------|
| 8 | `/edu-console` 全局弱點分析快速卡片為 alert() stub | 待開發 |
| 9 | `/exam/results` Layer 3 適用性評估 | 待 QA 架構師確認 |
| 10 | `/knowledge` 分享知識節點無 Scenario 且未實作 | 待開發 |
| 11 | `/knowledge` AI 教練灑花恭喜獎章動畫未實作 | 待開發 |

---

## 2. 本次處理項目

### Feature 10 L577-586 Scenario 誤導修正（P1）

**問題描述**：
Feature 10 尾部三個 Placeholder Rule 中，第一個 Rule「匯入學生名單按鈕顯示未實作提示」已與實際實作不符。`edu-console/page.tsx` 的 `ImportStudentModal` 已完整實作 CSV 匯入功能（CSV 解析、5 行預覽、consent checkbox、匯入結果統計），但 Scenario 仍描述為「即將推出」。

**修正內容**：

1. **project/features/10-B2B機構管理後台.feature**
   - 移除過時的 Rule「匯入學生名單按鈕顯示未實作提示」
   - 新增 Rule「機構管理後台匯入學生名單應開啟 CSV 匯入 Modal」含 3 個 Example Scenario：
     - 點擊按鈕開啟 Modal（含 CSV 上傳區域、下載範本按鈕、欄位說明）
     - 上傳 CSV 後顯示預覽表格與同意勾選（最多 5 行、同意勾選框、停用狀態按鈕）
     - 匯入成功後顯示結果統計（總筆數、新建帳號數、加入成員數、跳過重複數、群組列表）
   - 保留「派發模擬考卷與全局弱點分析卡片」和「匯出詳細報告」兩個 placeholder Rule（仍為 alert() stub）
   - 更新註解說明哪些功能已實作、哪些仍為 stub

2. **backend/tests/features/10-B2B機構管理後台.feature**
   - 同步更新，內容與 project/ 版本一致

3. **docs/ToDoList.md**
   - 將 Feature 10 L577-586 項目標記為 `[x]` 已完成

**未修改的 BDD Step Definitions**：
- `b2b_ui_actions.py` 中 `step_impl_click_import_students` 仍呼叫 placeholder endpoint
- 新增的 3 個 Scenario 使用了新的 Given/When/Then 步驟（如「系統應開啟 CSV 匯入 Modal」），需在後續開發中補充對應 step definitions（標記為 @frontend，屬前端 Playwright 測試範疇）

---

## 3. 未處理項目說明

以下項目因複雜度、風險或需求不適合在無人值守排程中處理：

- **ECPay 金流整合（P1）**：需第三方 API 整合、測試環境設定，風險過高
- **EPIC-035 AI inference 移植（P2）**：需跨頁面 UI 遷移，涉及多個 component
- **edu-console alert() stubs（P2/P3）**：需完整 modal 設計與後端 API 對接
- **Certi 情感表情 UI（P2）**：需動畫/表情系統設計
- **Layer 3 適用性評估（P3）**：需 QA 架構師判定，非自動化可決

---

## 4. 建議下次巡檢重點

1. P1 ECPay 整合進度追蹤
2. EPIC-035 AI inference 按鈕移植至 `/exam/workspace`
3. 為新增的 3 個 CSV 匯入 Scenario 補充 Playwright step definitions
