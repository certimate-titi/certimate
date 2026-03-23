Feature: 資源庫管理與連鎖清除防呆機制

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

  Rule: 後置（狀態）- 刪除 COMPLETED 資源時需彈出連鎖清除警告

    Example: 使用者嘗試刪除已完成解析的資源，系統彈出防呆確認
      When 使用者 "alice@example.com" 點擊刪除資源 1
      Then 系統應彈出防呆模態框
      And 模態框內容應警告：「此操作將同步刪除：① GCS 中的 .md 純文字紀錄、② pgvector 中的所有切塊向量、③ 衍生的心智圖知識節點、④ 相關聯的錯題排程紀錄。此操作無法復原。」

    Example: 使用者確認刪除後，系統依序執行連鎖清除
      Given 使用者已確認刪除資源 1 並勾選「我了解相關資料將永久清除」
      When 系統執行連鎖刪除
      Then 操作成功
      And GCS 中資源 1 的 .md 純文字紀錄應永久刪除
      And pgvector 中資源 1 關聯的所有 Embedding Chunks 應全數抹除
      And 資源 1 關聯的所有心智圖知識節點應標記為已刪除
      And 學習記憶排程中對應該資源考題的排程紀錄應連動撤銷

  Rule: 後置（狀態）- FAILED 資源可重新觸發解析，保留原始檔至成功為止

    Example: 對 FAILED 資源觸發重新解析後狀態重置為 PENDING，原始檔保留在 GCS
      When 使用者 "alice@example.com" 重新解析資源 3
      Then 操作成功
      And 資源 3 的狀態應重置為 "PENDING"
      And 資源 3 的原始 PDF 應仍保留於 GCS，等待重試完成

    Example: 重新解析成功後狀態更新為 COMPLETED，原始檔隨即從 GCS 刪除
      Given 資源 3 的狀態為 "PROCESSING"
      When 後端解析服務成功完成資源 3 的重試解析
      Then 資源 3 的狀態應更新為 "COMPLETED"
      And 資源 3 的原始 PDF 應從 GCS 永久刪除
      And 资源 3 應關聯至少一個新生成的心智圖知識節點

    Example: FAILED 資源刪除時無需彈出連鎖清除警告（尚無衍生資料）
      When 使用者 "alice@example.com" 刪除資源 3
      Then 操作成功
      And 資源 3 應標記為已刪除
      And 資源 3 的原始 PDF 應從 GCS 永久刪除

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
