Feature: 資源庫管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO      |
    And 系統中有以下資源：
      | 資源 ID | 使用者 ID | 名稱                  | 類型    | 狀態      | 上傳時間            |
      | 1       | 1        | AWS_SAA_官方手冊.pdf  | PDF     | COMPLETED | 2024-01-05 10:00:00 |
      | 2       | 1        | 雲端概論筆記.md       | MD      | COMPLETED | 2024-01-08 14:00:00 |
      | 3       | 1        | 解析失敗的資料.pdf    | PDF     | FAILED    | 2024-01-09 09:00:00 |
      | 4       | 2        | Bob的AWS筆記.pdf      | PDF     | COMPLETED | 2024-01-06 11:00:00 |
      | 5       | 1        | AWS架構影片           | YouTube | COMPLETED | 2024-01-10 16:00:00 |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能查看及管理自己的資源

    Example: 查詢自己的資源列表不應包含他人資源
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 資源列表應只包含資源 ID 1、2、3、5
      And 資源列表不應包含資源 ID 4

  Rule: 前置（狀態）- 刪除他人資源失敗

    Example: 刪除其他使用者的資源失敗
      When 使用者 "alice@example.com" 刪除資源 4
      Then 操作失敗
      And 錯誤訊息應為 "無存取此資源的權限"

  # ========== 後置條件 ==========

  Rule: 後置（回應）- 查詢資源列表應回傳完整屬性包含狀態標籤

    Example: 查詢資源列表取得完整資源資訊
      When 使用者 "alice@example.com" 查詢自己的資源列表
      Then 操作成功
      And 資源列表應包含以下資源資訊：
        | 資源 ID | 名稱                  | 類型    | 狀態      | 上傳時間            |
        | 1       | AWS_SAA_官方手冊.pdf  | PDF     | COMPLETED | 2024-01-05 10:00:00 |
        | 2       | 雲端概論筆記.md       | MD      | COMPLETED | 2024-01-08 14:00:00 |
        | 3       | 解析失敗的資料.pdf    | PDF     | FAILED    | 2024-01-09 09:00:00 |
        | 5       | AWS架構影片           | YouTube | COMPLETED | 2024-01-10 16:00:00 |

  Rule: 後置（狀態）- 刪除資源後相關聯的心智圖節點應一併軟刪除

    Example: 成功刪除 COMPLETED 狀態的資源後關聯心智圖節點一併移除
      When 使用者 "alice@example.com" 刪除資源 1
      Then 操作成功
      And 資源 1 應標記為已刪除
      And 資源 1 關聯的所有心智圖知識節點應標記為已刪除

    Example: 成功刪除 FAILED 狀態的資源
      When 使用者 "alice@example.com" 刪除資源 3
      Then 操作成功
      And 資源 3 應標記為已刪除

  Rule: 後置（回應）- 重新觸發 FAILED 資源解析應回傳新的排程任務資訊

    Example: 對 FAILED 資源觸發重新解析後狀態重置為 PENDING
      When 使用者 "alice@example.com" 重新解析資源 3
      Then 操作成功
      And 資源 3 的狀態應重置為 "PENDING"
      And 回應應包含新的排程任務 ID

  Rule: 後置（回應）- 搜尋資源時應依檔名與自動萃取的標籤進行篩選

    Example: 依關鍵字搜尋資源名稱取得符合結果
      When 使用者 "alice@example.com" 以關鍵字 "AWS" 搜尋資源列表
      Then 操作成功
      And 搜尋結果應包含資源 ID 1 和資源 ID 5
      And 搜尋結果不應包含資源 ID 2

    Example: 以標籤篩選資源取得符合結果
      Given 資源 1 帶有自動萃取的標籤 "EC2"、"S3"、"IAM"
      When 使用者 "alice@example.com" 以標籤 "EC2" 篩選資源列表
      Then 操作成功
      And 搜尋結果應包含資源 ID 1
