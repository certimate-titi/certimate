@backend
Feature: 意見反饋

  # 反饋類型 API enum 值：BUG | FEATURE_REQUEST | CONTENT_ERROR | OTHER
  # 反饋狀態 API enum 值：PENDING | REVIEWING | RESOLVED | CLOSED
  # 入口：全站頁尾（Footer）的「意見反饋」連結，路徑為 /feedback

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案  | 角色        | 狀態   |
      | 1        | alice@example.com    | FREE       | USER        | 已啟用 |
      | 2        | bob@example.com      | PRO_199    | USER        | 已啟用 |
      | 3        | admin@example.com    | FREE       | ADMIN       | 已啟用 |
    And 系統中有以下意見反饋紀錄：
      | 反饋 ID | 使用者 ID | 類型            | 主旨                    | 狀態       | 建立時間            |
      | FB-001  | 1        | BUG             | 模擬機考計時顯示異常     | PENDING    | 2026-03-20T10:00:00 |
      | FB-002  | 2        | FEATURE_REQUEST | 希望新增暗色模式         | REVIEWING  | 2026-03-22T09:00:00 |
      | FB-003  | 1        | CONTENT_ERROR   | 題目 Q-123 答案有誤      | RESOLVED   | 2026-03-15T08:00:00 |

  # ========== 頁尾連結入口 ==========

  Rule: 後置（回應）- 頁尾「意見反饋」連結應對所有訪客可見，並依登入狀態導向不同頁面

    Example: 已登入使用者點擊頁尾意見反饋連結後進入意見反饋頁
      Given 使用者 "alice@example.com" 已登入系統
      When 使用者點擊頁尾的「意見反饋」連結
      Then 系統應導向至 "/feedback" 頁面
      And 頁面應顯示意見反饋表單（包含類型、主旨、內容欄位）

    Example: 未登入訪客點擊頁尾意見反饋連結後被導向登入頁
      Given 使用者尚未登入
      When 使用者點擊頁尾的「意見反饋」連結
      Then 系統應導向至登入頁面
      And 登入成功後應自動重新導向至 "/feedback"

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 僅登入使用者可提交意見反饋

    Example: 未登入使用者直接呼叫反饋 API 被拒絕
      When 未登入的使用者直接呼叫意見反饋提交 API
      Then 操作失敗
      And HTTP 狀態碼應為 401

  Rule: 前置（參數）- 提交意見反饋必須提供必要欄位

    Scenario Outline: 缺少必要欄位時提交失敗
      When 使用者 "alice@example.com" 提交意見反饋，缺少 <缺少欄位>
      Then 操作失敗
      And 錯誤訊息應為 "必要欄位未填寫"

      Examples:
        | 缺少欄位 |
        | 類型     |
        | 主旨     |
        | 內容     |

  Rule: 前置（參數）- 主旨長度不得超過 100 字，內容不得超過 2000 字

    Example: 主旨超過 100 字時提交失敗
      When 使用者 "alice@example.com" 提交意見反饋，主旨長度為 101 個字元
      Then 操作失敗
      And 錯誤訊息應為 "主旨不得超過 100 個字元"

    Example: 內容超過 2000 字時提交失敗
      When 使用者 "alice@example.com" 提交意見反饋，內容長度為 2001 個字元
      Then 操作失敗
      And 錯誤訊息應為 "內容不得超過 2000 個字元"

  Rule: 前置（狀態）- 同一使用者於 1 小時內對相同主旨不可重複提交

    Example: 1 小時內重複提交相同主旨的意見反饋失敗
      Given 使用者 "alice@example.com" 於 30 分鐘前已提交主旨為 "模擬機考計時顯示異常" 的意見反饋
      When 使用者 "alice@example.com" 再次提交主旨為 "模擬機考計時顯示異常" 的意見反饋
      Then 操作失敗
      And 錯誤訊息應為 "您已於近期提交過相同主題的反饋，請稍後再試"

  # ========== 提交意見反饋 ==========

  Rule: 後置（狀態）- 成功提交後反饋應建立並回傳確認資訊

    Example: 使用者成功提交一則錯誤回報
      When 使用者 "alice@example.com" 提交意見反饋：
        | 欄位     | 值                        |
        | 類型     | BUG                       |
        | 主旨     | 測驗頁面無法正常捲動       |
        | 內容     | 在 Safari 瀏覽器上滾動題目清單時頁面會卡住 |
      Then 操作成功
      And 系統應建立新的反饋紀錄，狀態為 "PENDING"
      And 回應應包含新建立的 feedback_id
      And 系統應發送確認通知至 "alice@example.com"，主旨含「我們已收到您的意見反饋」

    Example: 使用者成功提交一則功能需求
      When 使用者 "bob@example.com" 提交意見反饋：
        | 欄位     | 值                    |
        | 類型     | FEATURE_REQUEST       |
        | 主旨     | 希望支援離線練習模式   |
        | 內容     | 在網路不穩時仍能作答，待連線後再同步成績 |
      Then 操作成功
      And 系統應建立新的反饋紀錄，狀態為 "PENDING"

  Rule: 後置（狀態）- 使用者可附加螢幕截圖（附件上傳，限 3 張，每張 ≤ 5 MB，格式 JPG/PNG）

    Example: 上傳符合規格的截圖附件成功
      When 使用者 "alice@example.com" 提交意見反饋時附加 2 張 PNG 截圖，各 2 MB
      Then 操作成功
      And 反饋紀錄應包含 2 個附件的儲存路徑

    Example: 上傳超過 5 MB 的截圖時提交失敗
      When 使用者 "alice@example.com" 提交意見反饋時附加 1 張 8 MB 的 PNG 截圖
      Then 操作失敗
      And 錯誤訊息應為 "附件大小不得超過 5 MB"

    Example: 上傳超過 3 張截圖時提交失敗
      When 使用者 "alice@example.com" 提交意見反饋時附加 4 張截圖
      Then 操作失敗
      And 錯誤訊息應為 "最多只能上傳 3 張截圖"

  # ========== 查看自己的意見反饋 ==========

  Rule: 後置（回應）- 使用者可查看自己提交的所有意見反饋清單

    Example: 使用者查看自己的意見反饋清單
      When 使用者 "alice@example.com" 查看自己的意見反饋清單
      Then 操作成功
      And 回應應包含 2 筆反饋（FB-001、FB-003）
      And 每筆紀錄應包含：
        | 欄位         | 說明               |
        | feedback_id  | 反饋唯一識別碼     |
        | type         | 反饋類型           |
        | subject      | 主旨               |
        | status       | 目前狀態           |
        | created_at   | 提交時間           |

    Example: 使用者不應看到其他使用者的反饋
      When 使用者 "alice@example.com" 查看自己的意見反饋清單
      Then 回應中不應包含反饋 "FB-002"（屬於 bob@example.com）

  Rule: 後置（回應）- 使用者可查看單筆反饋的完整內容與處理進度

    Example: 查看已解決反饋的詳細資訊
      When 使用者 "alice@example.com" 查看反饋 "FB-003" 的詳細資訊
      Then 操作成功
      And 回應應包含：
        | 欄位           | 值                       |
        | feedback_id    | FB-003                   |
        | type           | CONTENT_ERROR            |
        | subject        | 題目 Q-123 答案有誤       |
        | status         | RESOLVED                 |
        | admin_reply    | （管理員回覆內容，非空白） |
        | resolved_at    | （解決時間戳記）          |

  # ========== 管理員處理意見反饋 ==========

  Rule: 前置（狀態）- 僅 ADMIN 可存取所有使用者的意見反饋管理功能

    Example: 一般使用者嘗試存取意見反饋管理清單被拒絕
      When 使用者 "alice@example.com" 嘗試存取管理員意見反饋清單 API
      Then 操作失敗
      And 錯誤訊息應為 "權限不足"

  Rule: 後置（回應）- 管理員可查看全站所有意見反饋並依狀態篩選

    Example: 管理員查看所有 PENDING 狀態的反饋
      When 使用者 "admin@example.com" 查看所有狀態為 "PENDING" 的意見反饋
      Then 操作成功
      And 回應應包含 1 筆反饋（FB-001）

    Example: 管理員查看所有意見反饋清單（不篩選）
      When 使用者 "admin@example.com" 查看所有意見反饋清單
      Then 操作成功
      And 回應共包含 3 筆反饋

  Rule: 後置（狀態）- 管理員可更新反饋狀態並回覆使用者

    Example: 管理員將反饋標記為調查中並回覆
      When 使用者 "admin@example.com" 更新反饋 "FB-001"：
        | 欄位        | 值                                    |
        | 狀態        | REVIEWING                             |
        | 管理員回覆  | 感謝您的回報，我們已確認此問題並正在修復中 |
      Then 操作成功
      And 反饋 "FB-001" 的狀態應為 "REVIEWING"
      And 系統應發送通知至 "alice@example.com"，主旨含「您的意見反饋狀態已更新」
      And 系統應記錄審計日誌：
        | 欄位     | 值                                      |
        | action   | update_feedback_status                  |
        | target   | FB-001                                  |
        | details  | PENDING → REVIEWING，admin@example.com 回覆 |

    Example: 管理員將反饋標記為已解決
      When 使用者 "admin@example.com" 更新反饋 "FB-001"，狀態為 "RESOLVED"
      Then 操作成功
      And 反饋 "FB-001" 的狀態應為 "RESOLVED"
      And 反饋紀錄應包含 resolved_at 時間戳記

    Example: 管理員關閉無效反饋
      When 使用者 "admin@example.com" 更新反饋 "FB-001"，狀態為 "CLOSED"，原因為 "內容重複，已合併至 FB-002"
      Then 操作成功
      And 反饋 "FB-001" 的狀態應為 "CLOSED"

  Rule: 後置（回應）- 管理員可查看意見反饋統計摘要

    Example: 管理員查看反饋統計資料
      When 使用者 "admin@example.com" 查看意見反饋統計摘要
      Then 操作成功
      And 回應應包含：
        | 欄位              | 說明                     |
        | total_count       | 所有反饋總數             |
        | pending_count     | 待處理反饋數量           |
        | reviewing_count   | 處理中反饋數量           |
        | resolved_count    | 已解決反饋數量           |
        | top_category      | 最多反饋的類型（enum 值） |
        | avg_resolve_hours | 平均解決時間（小時）     |
