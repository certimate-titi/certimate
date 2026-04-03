---
name: no-direct-db-mock
description: Never insert mock/test data directly into DB — always go through the UI flow (e.g., CSV import button)
type: feedback
---

不要直接在資料庫建立 mock 測試資料。測試資料應透過 UI 流程（如匯入按鈕）匯入到 DB。

**Why:** 用戶認為測試應模擬真實使用流程，直接操作 DB 不是正確的測試方式，也無法驗證匯入功能本身是否正常。

**How to apply:** 當需要建立測試資料時，應先實作或使用對應的 UI 功能（如 CSV 匯入），製作符合格式的測試檔案，再透過 UI 操作完成匯入。
