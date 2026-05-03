@backend
Feature: 異常維修管理

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案 | 角色         |
      | 1        | super@certimate.com     | ULTRA    | SUPER_ADMIN  |
      | 2        | admin@certimate.com     | ULTRA    | ADMIN        |
    And 系統中有以下異常紀錄：
      | 異常 ID  | 錯誤類型                       | 發生次數 | 狀態    | 影響範圍      |
      | ERR-001  | Database Connection Timeout    | 100      | pending | 全站           |
      | ERR-002  | Vision OCR Parse Failure       | 5        | pending | AI 模組        |
    And 系統中有以下維修任務：
      | 任務 ID  | 名稱                   | 優先級 | 關聯異常 | 狀態    |
      | MNT-001  | 核心數據庫索引優化      | high   | ERR-001  | pending |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 僅 admin 與 super_admin 可存取異常維修管理

    Example: 一般用戶存取異常維修管理被拒絕
      Given 系統中有以下使用者帳號：
        | 使用者 ID | Email               | 訂閱方案 | 角色 |
        | 10       | alice@example.com   | FREE     | USER |
      When 使用者 "alice@example.com" 存取異常維修管理頁面
      Then 操作失敗，錯誤為「權限不足，無法存取異常維修管理」

  Rule: 前置（參數）- 建立維修任務必須提供必要參數

    Scenario Outline: 建立維修任務缺少 <缺少參數> 時失敗
      When 使用者 "batchfix-admin-9876@example.com" 建立維修任務，名稱為 <名稱>，優先級為 <優先級>
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數 | 名稱               | 優先級 |
        | 名稱     |                    | high   |
        | 優先級   | API Gateway 升級   |        |

  # ========== 異常追蹤 ==========

  Rule: 後置（回應）- 異常清單應按時間排序並包含完整屬性

    Example: 查看異常清單取得所有紀錄
      When 使用者 "batchfix-admin-9876@example.com" 查看異常追蹤清單
      Then 操作成功
      And 回應中每筆紀錄應包含：
        | 欄位             | 範例值                        |
        | error_id         | ERR-001                       |
        | error_type       | Database Connection Timeout   |
        | occurrence_count | 100                           |
        | status           | pending                       |
        | impact_scope     | 全站                          |
        | first_seen_at    | 2026-03-25 10:00:00           |
        | last_seen_at     | 2026-03-25 14:30:00           |

  Rule: 後置（狀態）- 相似錯誤應自動歸類彙整

    Example: 100 次相同 Database Timeout 被歸類為一筆彙整項目
      When 使用者 "batchfix-admin-9876@example.com" 查看異常追蹤清單
      Then 異常 "ERR-001" 的發生次數應為 100
      And 異常 "ERR-001" 應標記為「已歸類」

  Rule: 後置（狀態）- 更新異常狀態與指派應記錄審計日誌

    Example: 將異常標註為調查中並指派給技術小組
      When 使用者 "batchfix-admin-9876@example.com" 更新異常 "ERR-001"，狀態為 "investigating"，指派給 "技術小組"
      Then 操作成功
      And 異常 "ERR-001" 的狀態應為 "investigating"
      And 系統應記錄審計日誌：
        | 欄位     | 值                              |
        | action   | update_anomaly_status           |
        | target   | ERR-001                         |
        | details  | pending → investigating, 指派技術小組 |

  # ========== 維修任務看板 ==========

  Rule: 後置（狀態）- 建立維修任務後應出現在看板的待處理欄

    Example: 建立維修任務成功
      When 使用者 "batchfix-admin-9876@example.com" 建立維修任務：
        | 欄位            | 值                    |
        | name            | API Gateway 升級      |
        | priority        | medium                |
        | related_error   | ERR-002               |
        | estimated_hours | 2                     |
      Then 操作成功
      And 新任務的狀態應為 "pending"

  Rule: 後置（狀態）- 變更任務狀態應同步通知相關技術人員

    Example: 將任務從待處理移至進行中
      When 使用者 "batchfix-admin-9876@example.com" 更新維修任務 "MNT-001" 的狀態為 "in_progress"
      Then 操作成功
      And 任務 "MNT-001" 的狀態應為 "in_progress"
      And 系統應通知指派的技術人員

  # ========== 維修排程與通知 ==========

  Rule: 後置（狀態）- 建立維修排程後系統應在指定時間前自動發送通知

    Example: 建立維修排程並設定提前通知成功
      When 使用者 "super@certimate.com" 建立維修排程：
        | 欄位             | 值                    |
        | name             | API Gateway 升級      |
        | starts_at        | 2026-05-01T02:00:00   |
        | ends_at          | 2026-05-01T04:00:00   |
        | notify_channels  | email,banner          |
        | notify_targets   | all_subscribers       |
        | notify_before    | 24h,1h                |
      Then 操作成功
      And 系統應排定在 2026-04-30T02:00:00 與 2026-05-01T01:00:00 發送通知

  Rule: 後置（狀態）- 啟動全站維修模式後所有請求應導向維修頁面

    Example: 啟動全站緊急維護成功
      When 使用者 "super@certimate.com" 啟動全站維修模式，原因為 "緊急安全修補"，預計恢復時間為 "2026-03-25T18:00:00"
      Then 操作成功
      And 系統應通知所有在線用戶
      And 所有非管理後台的請求應導向維修頁面

  Rule: 後置（狀態）- 維修排程到達結束時間且檢查通過後應自動恢復

    Example: 維修結束時間到達後自動關閉維修模式
      Given 當前維修排程的結束時間為 "2026-05-01T04:00:00"
      And 維修健康檢查已通過
      When 系統偵測到結束時間已到達
      Then 系統應自動關閉維修模式
      And 用戶應能正常存取所有功能

  Rule: 後置（操作）- 提供「批次修復」一鍵將多筆異常一起標記為已修復

    # 落地紀錄（2026-05-03）：頁面 /super-admin/anomaly 新增多選 checkbox
    # + 「批次修復」按鈕；前端依序對每筆異常呼叫 PUT /admin/anomalies/{id}
    # body={"status":"resolved"}，部分失敗時保留勾選 + 紅色 icon。
    # 此處 backend 涵蓋每筆 PATCH 的後端正確性。

    Example: 多筆異常依序標記為已修復
      Given 系統中有以下異常紀錄：
        | 異常 ID            | 錯誤類型         | 發生次數 | 狀態    | 影響範圍 |
        | err_db_timeout_01 | DatabaseTimeout | 5     | pending | admin  |
        | err_db_timeout_02 | DatabaseTimeout | 3     | pending | admin  |
        | err_db_timeout_03 | DatabaseTimeout | 2     | pending | admin  |
      When 使用者 "admin@certimate.com" 更新異常 "err_db_timeout_01"，狀態為 "resolved"，指派給 "self"
      Then 操作成功
      When 使用者 "admin@certimate.com" 更新異常 "err_db_timeout_02"，狀態為 "resolved"，指派給 "self"
      Then 操作成功
      When 使用者 "admin@certimate.com" 更新異常 "err_db_timeout_03"，狀態為 "resolved"，指派給 "self"
      Then 操作成功
      And 異常 "err_db_timeout_01" 的狀態應為 "resolved"
      And 異常 "err_db_timeout_02" 的狀態應為 "resolved"
      And 異常 "err_db_timeout_03" 的狀態應為 "resolved"
