# ToDoList 定期巡檢紀錄 — 2026-04-19T02:41:03 UTC

## 巡檢結果：無可執行的待辦事項

### 掃描摘要

| 項目 | 狀態 | 說明 |
|------|------|------|
| GCP Billing Export 配置部署（P1） | ⏳ 待運維 | 程式碼已完成（2026-04-17），剩餘 3 項為 Cloud Run 部署操作，非程式碼任務 |
| 用戶管理前端修復（P1） | ✅ 完成 | 2026-04-17 |
| Prompt 模板前端修復（P1） | ✅ 完成 | 2026-04-17 |
| SSO 密碼重設流程 | ✅ 完成 | 2026-04-17 |
| RAG 物理級跳轉完善（P2） | ✅ 完成 | 2026-04-17 |
| 向量快取機制（P2） | ✅ 完成 | 2026-04-17 |
| 系統設定頁面重組（P3） | ✅ 完成 | 2026-04-17 |

### 待運維操作（無法自動處理）

GCP Billing Export 配置部署的 3 項待辦為基礎設施操作：

1. Cloud Run：設定 `GCP_BILLING_MODE=real` 環境變數
2. Cloud Run：掛載 Service Account key（workload identity）
3. 驗證 API：`GET /admin/cost/gcp/services` 回傳真實資料

以上需要 GCP Console 或 `gcloud` CLI 存取權限，屬人工運維範疇。

### 結論

所有程式碼層級的待辦事項均已完成。ToDoList 目前處於清空狀態，僅剩部署運維操作。
建議下次新增待辦事項時，將運維項目移至獨立的 `ops-checklist.md` 以區分。

---

*本紀錄由 TiTi Commander 定期巡檢排程自動產出*
