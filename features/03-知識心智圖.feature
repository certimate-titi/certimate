Feature: 知識心智圖

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO      |
      | 3        | carol@example.com  | ULTRA    |
    And 系統中有以下資源：
      | 資源 ID | 使用者 ID | 名稱                   | 類型    | 狀態        |
      | 1       | 1        | AWS_SAA_官方白皮書.pdf  | PDF     | COMPLETED   |
      | 2       | 2        | 雲端架構影片            | YouTube | COMPLETED   |
      | 3       | 1        | 未完成講義.pdf          | PDF     | PROCESSING  |
    And 系統中有以下心智圖知識節點：
      | 節點 ID | 資源 ID | 父節點 ID | 名稱               | 掌握度顏色 |
      | 1       | 1       | null      | AWS 核心服務        | 灰色       |
      | 2       | 1       | 1         | EC2 運算服務        | 紅色       |
      | 3       | 1       | 1         | S3 儲存服務         | 綠色       |
      | 4       | 1       | 1         | IAM 身分管理        | 紅色       |
      | 5       | 2       | null      | 高可用架構設計      | 灰色       |
      | 6       | 2       | 5         | Load Balancer 配置  | 灰色       |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能查看狀態為 COMPLETED 的資源的心智圖

    Example: 查看尚在 PROCESSING 狀態的資源心智圖失敗
      When 使用者 "alice@example.com" 查看資源 3 的心智圖
      Then 操作失敗
      And 錯誤訊息應為 "資源尚未解析完成，請稍後再試"

  Rule: 前置（狀態）- 只能查看自己上傳的資源心智圖

    Example: 查看其他使用者資源的心智圖失敗
      When 使用者 "alice@example.com" 查看資源 2 的心智圖
      Then 操作失敗
      And 錯誤訊息應為 "無存取此資源的權限"

  # ========== 後置條件 ==========

  Rule: 後置（回應）- 查看心智圖應回傳完整的節點樹狀結構與各節點的掌握度顏色

    Example: 成功查看 PDF 資源的心智圖節點樹
      When 使用者 "alice@example.com" 查看資源 1 的心智圖
      Then 操作成功
      And 心智圖應包含以下節點：
        | 節點 ID | 名稱          | 父節點 ID | 掌握度顏色 |
        | 1       | AWS 核心服務  | null      | 灰色       |
        | 2       | EC2 運算服務  | 1         | 紅色       |
        | 3       | S3 儲存服務   | 1         | 綠色       |
        | 4       | IAM 身分管理  | 1         | 紅色       |

  Rule: 後置（回應）- 點擊 PDF 節點應回傳對應的文字內容與頁碼溯源資訊

    Example: 點擊 PDF 來源節點時溯源面板顯示頁碼與原文
      When 使用者 "alice@example.com" 點擊資源 1 的心智圖節點 2
      Then 操作成功
      And 溯源面板應顯示：
        | 欄位     | 值                               |
        | 來源頁碼 | 第 12 頁                         |
        | 原文片段 | EC2 提供可調整規模的運算容量...  |

  Rule: 後置（回應）- 點擊 YouTube 節點應回傳對應的影片時間戳記

    Example: 點擊 YouTube 來源節點時溯源面板顯示影片時間點
      When 使用者 "bob@example.com" 點擊資源 2 的心智圖節點 6
      Then 操作成功
      And 溯源面板應顯示：
        | 欄位       | 值                  |
        | 影片時間戳 | 00:08:32            |
        | 節點名稱   | Load Balancer 配置  |

  Rule: 後置（狀態）- 測驗完成後節點應依答對率自動更新掌握度顏色

    Example: 答對率高於 80% 時節點顏色更新為綠色
      Given 使用者 "alice@example.com" 完成一次包含節點 2 相關題目的測驗
      And 節點 2 的答對率為 85%
      When 系統重新計算節點 2 的掌握度
      Then 節點 2 的掌握度顏色應更新為 "綠色"

    Example: 答對率低於 60% 時節點顏色更新為紅色
      Given 使用者 "alice@example.com" 完成一次包含節點 3 相關題目的測驗
      And 節點 3 的答對率為 45%
      When 系統重新計算節點 3 的掌握度
      Then 節點 3 的掌握度顏色應更新為 "紅色"

  Rule: 後置（回應）- 資源列表支援卡片模式與列表模式切換

    # 此為前端 UI 偏好設定，無需 API 儲存；切換後重新整理頁面恢復預設（列表模式）。

    Example: 切換至卡片模式時資源以 2 欄格狀顯示
      Given 使用者 "alice@example.com" 已在知識庫頁面
      When 使用者點擊「卡片模式」切換按鈕
      Then 左側資源面板應以 2 欄格狀排列顯示資源卡片
      And 每張卡片應顯示資源的來源類型 icon、標題與來源類型標籤

    Example: 切換至列表模式時資源以單列顯示
      Given 使用者 "alice@example.com" 目前在知識庫頁面且為卡片模式
      When 使用者點擊「列表模式」切換按鈕
      Then 左側資源面板應以單列方式顯示資源項目
      And 每列應顯示資源 icon、標題、來源類型與解析狀態

  Rule: 後置（回應）- ULTRA 方案用戶可查看 Notion 與 Google Drive 同步設定

    Example: ULTRA 用戶可存取同步設定區塊
      When 使用者 "carol@example.com" 查看資源 1 的心智圖同步設定
      Then 操作成功
      And 回應應包含 Notion 整合設定選項
      And 回應應包含 Google Drive 整合設定選項

    Example: FREE 用戶無法存取同步設定區塊
      When 使用者 "alice@example.com" 查看資源 1 的心智圖同步設定
      Then 操作失敗
      And 錯誤訊息應為 "此功能僅限 ULTRA 方案用戶使用"
