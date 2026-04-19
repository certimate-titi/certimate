# 定期巡檢紀錄 — 2026-04-20T05:12 (UTC+8)

## 巡檢摘要

**執行時間**：2026-04-20 05:12 (UTC+8)
**觸發方式**：排程任務自動執行（check-todo）
**巡檢結果**：無可自動處理的待辦程式碼任務

---

## ToDoList.md 待辦事項檢查

### 唯一未完成項目：GCP Billing Export 配置部署（P1）

**狀態**：程式碼已完成（2026-04-17），剩餘為運維操作

| # | 待辦項目 | 類型 | 可自動處理 | 說明 |
|---|---------|------|-----------|------|
| 1 | Cloud Run：設定 `GCP_BILLING_MODE=real` | 運維 | ❌ | 需 GCP Console 或 gcloud CLI |
| 2 | Cloud Run：掛載 Service Account key（workload identity） | 運維 | ❌ | 需 GCP IAM 設定 |
| 3 | 驗證 API：`GET /admin/cost/gcp/services` 回傳真實資料 | 驗證 | ❌ | 需部署完成後才能驗證 |

**結論**：三項皆為 GCP 基礎設施運維操作，無法透過排程任務自動完成，需人工介入。

### 其他已完成項目（共 13 項）

所有其他待辦事項均已標記為 ✅ 完成，涵蓋：
- 題目分類（Bloom's Taxonomy）
- 考古題爬蟲
- EDU 學生訂閱衝突處置
- EDU 學生邀請信密碼設定流程
- Feature Conflicts 決議
- Prompt 模板管理（DBML + Feature + BDD + 前後端）
- 資料庫保護與管理
- 基礎設施安全層
- LLM 防火牆 + 任務佇列隔離
- Feature 32/33 節點練習模式 + 成本監控
- RAG 資料流程差異分析 + 平台管理功能審查
- 用戶管理前端修復
- Prompt 模板前端修復
- SSO 密碼重設流程
- RAG 物理級跳轉完善
- 向量快取機制
- 系統設定頁面重組

---

## Git 狀態

- 工作目錄乾淨（僅 `frontend/next-env.d.ts` 有微小變動 + `.claude/scheduled_tasks.lock`）
- 最近提交：`80d8515 Clarify coupon creation form with labels and examples`

---

## 建議行動

1. **GCP 部署**：請開發者手動執行 GCP Billing Export 的三項運維操作
2. **新需求**：ToDoList.md 中可新增下一階段開發待辦事項
