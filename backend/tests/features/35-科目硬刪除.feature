@fullstack
Feature: 科目硬刪除（Backend API）

  # 對應 project/features/35-科目硬刪除.feature 的後端契約。
  # 純 UI 行為（modal 文案 / disabled 狀態）保留在 project/features/ 不在此 file。
  # 後端契約：
  #   GET    /api/v1/subjects/{id}/delete-preview  → SUPER_ADMIN only
  #   DELETE /api/v1/subjects/{id}/hard            → SUPER_ADMIN only，cascade
  #   寫入 admin_audit_logs（action=SUBJECT_HARD_DELETED）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案 | 角色        |
      | 1         | super@certimate.com  | FREE     | SUPER_ADMIN |
      | 2         | admin@certimate.com  | FREE     | ADMIN       |
      | 3         | alice@example.com    | PRO_199  | USER        |
    And 存在科目 "subj_01" 名稱 "不動產經紀人"，含 5 個 knowledge_node、3 個 exam
    And 存在科目 "subj_02" 名稱 "金融理財規劃"，含 2 個 knowledge_node、1 個 exam

  Rule: 硬刪科目 — 權限與成功路徑

    @fullstack
    Example: super-admin 取得 delete-preview → 200 + cascade_count 結構正確
      When super-admin "super@certimate.com" 呼叫 GET /api/v1/subjects/subj_01/delete-preview
      Then 系統應回傳 200
      And 回應的 subject_name 應為 "不動產經紀人"
      And 回應 cascade_count 應包含欄位 "knowledge_nodes"、"exams"、"resources"
      And 回應 cascade_count.knowledge_nodes 應為 5
      And 回應 cascade_count.exams 應為 3

    @fullstack
    Example: super-admin 硬刪科目 → 200 + DB row 不存在 + audit_log 寫入
      When super-admin "super@certimate.com" 呼叫 DELETE /api/v1/subjects/subj_01/hard
      Then 系統應回傳 200
      And 資料庫中科目 subj_01 的 row 不應存在
      And 資料庫中 knowledge_nodes 表不應存在 subject_id 為 subj_01 的 row
      And 資料庫中 exams 表不應存在 subject_id 為 subj_01 的 row
      And 資料庫中 admin_audit_logs 應有一筆 action 為 "SUBJECT_HARD_DELETED" 且 target_id 為 subj_01 的紀錄

    @fullstack
    Example: 非 super-admin（admin）呼叫 DELETE /hard → 403
      When 使用者 "admin@certimate.com" 呼叫 DELETE /api/v1/subjects/subj_01/hard
      Then 系統應回傳 403

    @fullstack
    Example: 一般用戶呼叫 DELETE /hard → 403
      When 使用者 "alice@example.com" 呼叫 DELETE /api/v1/subjects/subj_01/hard
      Then 系統應回傳 403

    @fullstack
    Example: 未認證請求 DELETE /hard → 401 或 403（FastAPI security）
      When 未認證使用者呼叫 DELETE /api/v1/subjects/subj_01/hard
      Then 系統應回傳 401 或 403

  Rule: 硬刪後查詢

    @fullstack
    Example: 硬刪後重新查詢 delete-preview → 404
      Given super-admin "super@certimate.com" 已硬刪科目 subj_02
      When super-admin "super@certimate.com" 呼叫 GET /api/v1/subjects/subj_02/delete-preview
      Then 系統應回傳 404
