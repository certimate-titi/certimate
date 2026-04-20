# PRD-034 預載科目解耦式 Fork 模型

**狀態**：Draft
**作者**：產品經理（TiTi Commander）
**建立日期**：2026-04-20
**優先級**：P1
**相關**：PRD-033（多租戶資源/科目完整化）、Feature 23（考古題題庫管理）、Feature 03（知識心智圖）

---

## 1. 背景

PRD-033 引入 `scope = platform | personal | institution | shared` 與 `subject_default_resources` 關聯表，讓平台可提供「預載科目」（如 iPAS、高普考、金融證照），供用戶快速起步。但目前未定義「用戶採用後、platform 端後續變動」的傳播語義，也未定義「用戶端對該科目內資源的主權」。

目前行為不確定，未來可能踩到：
- 平台改題 → 用戶正在做的模擬考題目被動變更
- 平台刪題 → 用戶的錯題紀錄失去 FK
- 用戶想刪除平台預載題 → 目前無法（scope=platform 不屬於用戶）

## 2. 設計原則

**解耦式 Fork**：預載科目只是「模板」。用戶選科當下一次性複製到個人 scope，之後完全解耦。

- 用戶端：版本、更新、通知、合併一概不可見
- 平台端：admin 可草稿/發布/回滾，但只影響「未來選科」的新用戶
- 心智圖：動態依用戶當前擁有資源生成；用戶刪光資源 → 空心智圖為合法狀態

## 3. 用戶故事

### US-01 用戶選平台預載科目 → 一次性 Fork
**作為** 考生
**我希望** 選擇平台預載的「iPAS AI 應用規劃師（初級）」時，系統把該科目的預載資源與心智圖節點複製到我的帳號
**以便** 立即開始學習、又能自由管理這些資源

**驗收**：
- 選科完成後，該科目資源屬於我（scope=personal），可編輯刪除
- 選科完成後，該科目心智圖已建立（依複製的節點）
- 複製過程 UI 顯示進度；完成後跳轉至心智圖頁
- 複製失敗自動 rollback（DB + GCS）

### US-02 用戶刪除科目內資源 → 心智圖連帶更新
**作為** 考生
**我希望** 刪除不需要的資源時，對應的知識節點自動移除、心智圖跟著變
**以便** 心智圖始終反映我當前擁有的學習材料

**驗收**：
- 刪資源 → 該資源專屬的 nodes 一併刪除（cascade）
- Merged node（被多資源引用）引用計數扣 1，歸零才刪
- 刪光所有資源 → 心智圖為空（合法空態，非錯誤）

### US-03 平台管理員編輯預載科目 → 草稿/發布/回滾
**作為** 平台管理員
**我希望** 編輯預載科目時先存草稿，確認後一鍵發布，若發布後發現問題可回滾
**以便** 維護題庫品質且能快速止損

**驗收**：
- 編輯時狀態為 draft，不影響現有用戶（既有選科用戶早已 fork 完成，完全不受影響）
- 發布時 `subjects.version` +1、`published_at` 更新；僅影響「未來選科」的新用戶
- 回滾：還原為前一版本（重設 version、published_at）
- UI 顯示「此發布將影響 N 位未來選科用戶」（恆為 0 位現有用戶受影響）

## 4. 功能範圍

| 功能 | 範圍 |
|------|------|
| **選科 Fork** | 用戶新增科目時若綁定 platform subject，觸發 `subject_fork_service.fork(platform_subject_id, user_id)`：複製 `subject_default_resources` 的 resources + GCS 檔案 + platform knowledge_nodes，FK 重指到新的 user resources |
| **Cascade 刪除** | `resource_service.delete_resource` 擴展：扣減相關 node.source_resource_count；歸零即刪，否則保留 |
| **Admin 草稿/發布/回滾** | 新增 `platform_subject_admin_service` + 3 個 API；UI 顯示版本歷史、影響範圍預覽 |
| **心智圖動態** | 無需改動 — 既有 knowledge_nav_service 已依 subject_id 過濾，fork 後節點屬用戶，自然正確 |

## 5. 非功能需求

- **原子性**：fork 全程包在 DB transaction；檔案複製失敗 → 清掉已複製的 GCS 檔案 + rollback transaction
- **效能**：fork 預載資源（典型：5 個 PDF + 30 個 nodes）< 5 秒；超過 10 秒 UI 要顯示進度
- **RLS**：fork 後資源 tenant_id = user tenant（沿用 PUBLIC_B2C_TENANT_ID）
- **儲存**：GCS 檔案複製用 `copy_blob` 不重新上傳
- **冪等性**：同一用戶重複選同 platform subject 應拒絕（409 Conflict）

## 6. 資料模型變更

```sql
-- Migration 065
ALTER TABLE subjects ADD COLUMN version INT NOT NULL DEFAULT 1;
ALTER TABLE subjects ADD COLUMN published_at TIMESTAMPTZ;
ALTER TABLE knowledge_nodes ADD COLUMN source_resource_count INT NOT NULL DEFAULT 1;
-- Backfill: existing nodes assume 1 source
```

## 7. API 契約

| Method | Path | 授權 | 說明 |
|--------|------|------|------|
| POST | `/api/v1/subjects/{platform_subject_id}/fork-from-platform` | User | 觸發 fork；回傳新建立的 user subject_id |
| PUT | `/api/v1/admin/platform-subjects/{id}/draft` | Admin | 更新 draft 內容（resources / nodes / exam_subject_codes） |
| POST | `/api/v1/admin/platform-subjects/{id}/publish` | Admin | 發布 draft → version +1 |
| POST | `/api/v1/admin/platform-subjects/{id}/rollback` | Admin | 回滾至前一版本 |
| GET | `/api/v1/admin/platform-subjects/{id}/versions` | Admin | 列出版本歷史 |

## 8. 成功指標

- 選科 fork 成功率 ≥ 99.5%（失敗 rollback 乾淨）
- 用戶投訴「為什麼我刪不了題目」歸零
- Admin 誤發布事故可於 30 秒內回滾

## 9. 風險與已知限制

- **儲存成本上升**：每用戶選科複製 ~ 5 PDF（20 MB）。若 10k 用戶採 iPAS 則 200 GB。需監控 GCS 用量。
- **考古題不複製**：沿用 `exam_subject_codes` 動態映射 — admin 改考古題會影響所有用戶（這是可接受的，考古題本質是公共歷史資料）
- **版本號對用戶透明**：用戶永遠看不到「我綁的是 v1」— 若未來要引入 migration 工具（讓舊用戶升級到新版），需額外 PRD

## 10. 不在本 PRD 範圍

- 用戶主動「重置科目到 platform 最新版」功能
- 用戶端看到「此科目有新版可用」通知
- Admin 批次對所有 platform subjects 做操作
- platform subject 之間的繼承/巢狀結構
