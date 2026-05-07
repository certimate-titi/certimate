@fullstack
Feature: 資源硬刪除（Backend API）

  # 對應 project/features/36-資源硬刪除.feature 的後端契約。
  # UI modal 行為留在 project/features/。
  # 後端契約：
  #   GET    /api/v1/resources/{id}/delete-preview  → owner only
  #   DELETE /api/v1/resources/{id}                 → owner only，cascade
  #   寫入 admin_audit_logs（action=RESOURCE_HARD_DELETED）

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email             | 訂閱方案 | 角色 |
      | 1         | alice@example.com | PRO_199  | USER |
      | 2         | bob@example.com   | PRO_199  | USER |
    And 存在科目 "subj_res" 名稱 "資源測試科目"，含 0 個 knowledge_node、0 個 exam
    And 使用者 "alice@example.com" 在科目 "subj_res" 擁有資源 "res_001" 名稱 "AWS_SAA手冊.pdf"，含 12 個 chunk
    And 使用者 "bob@example.com" 在科目 "subj_res" 擁有資源 "res_002" 名稱 "Bob的筆記.pdf"，含 8 個 chunk

  Rule: 擁有者硬刪資源

    @fullstack
    Example: 擁有者取得 delete-preview → 200 + cascade_count 結構正確
      When 使用者 "alice@example.com" 呼叫 GET /api/v1/resources/res_001/delete-preview
      Then 系統應回傳 200
      And 回應的 resource_name 應為 "AWS_SAA手冊.pdf"
      And 回應 cascade_count 應包含欄位 "resource_chunks"、"resource_parse_jobs"、"resource_scaffolds"
      And 回應 cascade_count.resource_chunks 應為 12

    @fullstack
    Example: 擁有者硬刪資源 → 200 + DB row 與子表 cascade 一併消失 + audit_log 寫入
      When 使用者 "alice@example.com" 呼叫 DELETE /api/v1/resources/res_001
      Then 系統應回傳 200
      And 資料庫中 resources 表的 res_001 row 不應存在
      And 資料庫中 resource_chunks 表不應存在任何 resource_id 為 res_001 的 row
      And 資料庫中 admin_audit_logs 應有一筆 action 為 "RESOURCE_HARD_DELETED" 且 target_id 為 res_001 的紀錄

    @fullstack
    Example: 非擁有者嘗試刪除他人資源 → 200 + 寫入 UserHiddenResource（軟隱藏）
      # 設計變更（2026-05-07）：知識庫頁本就將同 subject 全部 resources 顯示給訂閱者，
      # 「不洩露存在性」invariant 不成立。改為非擁有者刪除即軟隱藏，
      # 解決「看得到刪不掉」的 UX bug（Cloud Logging 9 筆 404）。
      When 使用者 "alice@example.com" 呼叫 DELETE /api/v1/resources/res_002
      Then 系統應回傳 200
      And 資料庫中 user_hidden_resources 應有 user_id 為 "alice@example.com" 且 resource_id 為 res_002 的 row

    @fullstack
    Example: 未認證使用者刪除資源 → 401 或 403
      When 未認證使用者呼叫 DELETE /api/v1/resources/res_001
      Then 系統應回傳 401 或 403

  Rule: 硬刪後重新查詢

    @fullstack
    Example: 硬刪後 delete-preview 回傳 404
      Given 使用者 "alice@example.com" 已硬刪資源 res_001
      When 使用者 "alice@example.com" 呼叫 GET /api/v1/resources/res_001/delete-preview
      Then 系統應回傳 404
