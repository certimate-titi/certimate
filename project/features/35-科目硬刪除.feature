@fullstack
Feature: 科目硬刪除

  # 注意：硬刪除科目為 P0 功能，僅 super-admin 角色可執行
  # 硬刪除 = 完全 cascade：knowledge_nodes / exams / questions / answers
  # / wrong_answers / resources / resource_chunks / resource_scaffolds
  # / node_mastery / learning_journeys 一併刪除
  # 執行前需二次確認 modal，必須輸入「確認刪除」文字才可送出

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                    | 訂閱方案   | 角色        |
      | 1        | super@certimate.com      | FREE       | SUPER_ADMIN |
      | 2        | admin@certimate.com      | FREE       | ADMIN       |
      | 3        | alice@example.com        | PRO_199    | USER        |
    And 系統中有以下科目：
      | 科目 ID | 名稱          | 知識節點數 | 考試數 | 學習旅程數 |
      | subj_01 | 不動產經紀人  | 5          | 3      | 2          |
      | subj_02 | 金融理財規劃  | 2          | 1      | 0          |
    And 科目 subj_01 含以下題目與答題紀錄：
      | 問題數 | 答題紀錄數 | 學習鷹架數 |
      | 24     | 120        | 3          |

  # ========== super-admin 硬刪科目 ==========

  Rule: super-admin 硬刪科目

    @fullstack
    Example: super-admin 點擊刪除科目 → 收到連帶筆數預覽 → 確認 → 204 + DB row 消失
      Given 使用者 "super@certimate.com" 已登入
      When 使用者在科目管理頁面點擊科目 "subj_01" 的刪除按鈕
      Then 系統應顯示二次確認 modal
      And modal 標題應為「永久刪除科目：不動產經紀人」
      And modal 應顯示連帶刪除筆數預覽：
        | 類型             | 筆數 |
        | 知識節點         | 5    |
        | 考試             | 3    |
        | 題目             | 24   |
        | 答題紀錄         | 120  |
        | 學習鷹架         | 3    |
        | 學習旅程         | 2    |
      And modal 警告文字應包含「此操作無法復原」
      When 使用者在 modal 確認輸入框填入「確認刪除」並點擊「永久刪除」按鈕
      Then 系統應呼叫 DELETE /api/v1/admin/subjects/{subj_01} 並收到 204
      And 資料庫中科目 subj_01 的 row 不應存在
      And 頁面科目列表中不應出現「不動產經紀人」

    @fullstack
    Example: 確認輸入框文字不符時送出按鈕應維持 disabled
      Given 使用者 "super@certimate.com" 已登入
      And 科目 subj_01 的刪除確認 modal 已開啟
      When 使用者在 modal 確認輸入框填入「刪除」（不完整）
      Then modal 中的「永久刪除」按鈕應保持 disabled
      And 系統不應發出 DELETE 請求

    @fullstack
    Example: 非 super-admin 嘗試刪除科目 → 403
      Given 使用者 "admin@certimate.com" 已登入
      When 使用者以 ADMIN 身份呼叫 DELETE /api/v1/admin/subjects/subj_01
      Then 系統應回傳 403
      And 錯誤訊息應為「此操作需要 SUPER_ADMIN 權限」

    @fullstack
    Example: 一般用戶嘗試刪除科目 → 403
      Given 使用者 "alice@example.com" 已登入
      When 使用者以 USER 身份呼叫 DELETE /api/v1/admin/subjects/subj_01
      Then 系統應回傳 403

  # ========== 硬刪 cascade 驗證 ==========

  Rule: 硬刪科目後所有 cascade 資料同時消失

    @fullstack
    Example: 硬刪科目後 knowledge_nodes 與 exams 同時消失
      Given 使用者 "super@certimate.com" 已登入
      And 科目 subj_01 擁有知識節點 [node_001, node_002] 以及考試 [exam_001]
      When 使用者確認刪除科目 subj_01
      Then 資料庫中 knowledge_nodes 表不應存在 node_001 或 node_002
      And 資料庫中 exams 表不應存在 exam_001
      And 資料庫中 resource_chunks 關聯 subj_01 的 row 應全數消失
      And 資料庫中 node_mastery 關聯 subj_01 的 row 應全數消失

    @fullstack
    Example: 硬刪後重新查詢科目 API 回傳 404
      Given 使用者 "super@certimate.com" 已登入
      And 科目 subj_02 已被硬刪除
      When 使用者呼叫 GET /api/v1/subjects/subj_02
      Then 系統應回傳 404
