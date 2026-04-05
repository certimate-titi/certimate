Feature: 資源庫管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO      |
    And 系統中有以下資源庫資源：
      | 資源 ID | 使用者 ID | 名稱                  | 類型    | 狀態      |
      | 1       | 1        | AWS_SAA_官方手冊.pdf  | pdf     | COMPLETED |
      | 2       | 1        | 雲端概論筆記.md       | markdown| COMPLETED |
      | 3       | 1        | 解析失敗的資料.pdf    | pdf     | FAILED    |
      | 4       | 2        | Bob的AWS筆記.pdf      | pdf     | COMPLETED |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能查看及管理自己的資源

    Example: 查詢自己的資源列表成功
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 資源列表數量應為 3

  Rule: 前置（狀態）- 刪除他人資源失敗

    Example: 刪除其他使用者的資源失敗
      When 使用者 "alice@example.com" 刪除資源 4
      Then 操作失敗，錯誤為「無存取此資源的權限」

  # ========== 搜尋 ==========

  Rule: 後置（回應）- 搜尋資源時應依檔名進行篩選

    Example: 依關鍵字搜尋資源名稱取得符合結果
      When 使用者 "alice@example.com" 以關鍵字 "AWS" 搜尋資源列表
      Then 操作成功
      And 資源列表數量應為 1

  # ========== 重新解析 ==========

  Rule: 後置（狀態）- FAILED 資源可重新觸發解析

    Example: 對 FAILED 資源觸發重新解析後狀態重置為 PENDING
      When 使用者 "alice@example.com" 重新解析資源 3
      Then 操作成功
      And 資源 3 的狀態應為 "PENDING"

  Rule: 前置（狀態）- 處理中的資源不可重複觸發解析

    Example: 對 PENDING 狀態的資源觸發重新解析應被拒絕
      When 使用者 "alice@example.com" 重新解析資源 3
      Then 操作成功
      When 使用者 "alice@example.com" 重新解析資源 3
      Then 操作失敗
      And 錯誤訊息應為 "資源正在處理中，請稍後再試"

  # ========== 刪除 ==========

  Rule: 後置（狀態）- FAILED 資源可直接刪除

    Example: 刪除 FAILED 資源成功
      When 使用者 "alice@example.com" 刪除資源 3
      Then 操作成功
