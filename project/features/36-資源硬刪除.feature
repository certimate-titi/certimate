@fullstack
Feature: 資源硬刪除

  # 資源擁有者可永久刪除自己上傳的資源
  # 硬刪除 = 完全 cascade：resource_chunks / resource_scaffolds
  # / resource_parse_jobs / question_candidates 一併刪除
  # 執行前需二次確認 modal，必須輸入「確認刪除」文字才可送出
  # 既有 deleted_at IS NOT NULL 軟刪資料一次性 purge 見 CLI 腳本規格

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案  | 角色        |
      | 1        | alice@example.com       | PRO_199   | USER        |
      | 2        | bob@example.com         | PRO_199   | USER        |
      | 3        | super@certimate.com     | FREE      | SUPER_ADMIN |
    And 系統中有以下資源：
      | 資源 ID  | 擁有者 Email      | 名稱              | 狀態      | chunks 數 | scaffolds 數 | parse_jobs 數 | candidates 數 |
      | res_001  | alice@example.com | AWS_SAA手冊.pdf   | COMPLETED | 12        | 3            | 1             | 5             |
      | res_002  | bob@example.com   | Bob的筆記.pdf     | COMPLETED | 8         | 2            | 1             | 3             |
      | res_003  | alice@example.com | 解析失敗的檔案.pdf | FAILED    | 0         | 0            | 1             | 0             |

  # ========== 資源擁有者硬刪自己的資源 ==========

  Rule: 資源擁有者硬刪自己上傳的資源

    @fullstack
    Example: 擁有者點擊刪除資源 → 連帶筆數預覽 → 輸入確認 → 204 + DB row 消失
      Given 使用者 "alice@example.com" 已登入
      When 使用者在資源庫頁面點擊資源 "res_001" 的刪除按鈕
      Then 系統應顯示二次確認 modal
      And modal 標題應為「永久刪除資源：AWS_SAA手冊.pdf」
      And modal 應顯示連帶刪除筆數預覽：
        | 類型             | 筆數 |
        | 知識切塊         | 12   |
        | 學習鷹架         | 3    |
        | 解析任務         | 1    |
        | 題目候選         | 5    |
      And modal 警告文字應包含「此操作無法復原」
      When 使用者在 modal 確認輸入框填入「確認刪除」並點擊「永久刪除」按鈕
      Then 系統應呼叫 DELETE /api/v1/resources/{res_001} 並收到 204
      And 資料庫中 resources 表的 res_001 row 不應存在
      And 頁面資源列表中不應出現「AWS_SAA手冊.pdf」

    @fullstack
    Example: 確認輸入框文字錯誤時送出按鈕應維持 disabled
      Given 使用者 "alice@example.com" 已登入
      And 資源 res_001 的刪除確認 modal 已開啟
      When 使用者在 modal 確認輸入框填入「刪除確認」（順序錯誤）
      Then modal 中的「永久刪除」按鈕應保持 disabled
      And 系統不應發出 DELETE 請求

    @fullstack
    Example: 非擁有者嘗試刪除他人資源 → 403
      Given 使用者 "alice@example.com" 已登入
      When 使用者呼叫 DELETE /api/v1/resources/res_002
      Then 系統應回傳 403
      And 錯誤訊息應為「無存取此資源的權限」

    @fullstack
    Example: 未認證用戶嘗試刪除資源 → 401
      Given 使用者未登入
      When 使用者呼叫 DELETE /api/v1/resources/res_001
      Then 系統應回傳 401

  # ========== 硬刪 cascade 驗證 ==========

  Rule: 硬刪資源後 chunks / scaffolds / parse_jobs 同時消失

    @fullstack
    Example: 硬刪 COMPLETED 資源後所有關聯子資料同時消失
      Given 使用者 "alice@example.com" 已登入
      And 資源 res_001 存在 12 個 resource_chunks、3 個 resource_scaffolds、1 個 parse_job、5 個 question_candidates
      When 使用者確認刪除資源 res_001
      Then 資料庫中 resource_chunks 表不應存在任何關聯 res_001 的 row
      And 資料庫中 resource_scaffolds 表不應存在任何關聯 res_001 的 row
      And 資料庫中 resource_parse_jobs 表不應存在任何關聯 res_001 的 row
      And 資料庫中 question_candidates 表不應存在任何關聯 res_001 的 row

    @fullstack
    Example: 硬刪 FAILED 資源後 parse_job 同時消失（雖無 chunks）
      Given 使用者 "alice@example.com" 已登入
      And 資源 res_003 狀態為 FAILED，存在 1 個 parse_job，0 個 chunks
      When 使用者確認刪除資源 res_003
      Then 資料庫中 resources 表的 res_003 row 不應存在
      And 資料庫中 resource_parse_jobs 表不應存在任何關聯 res_003 的 row

    @fullstack
    Example: 硬刪後重新查詢資源 API 回傳 404
      Given 使用者 "alice@example.com" 已登入
      And 資源 res_001 已被硬刪除
      When 使用者呼叫 GET /api/v1/resources/res_001
      Then 系統應回傳 404
