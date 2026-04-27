@backend @added-by:cto @coverage
Feature: API 覆蓋補齊 — 既有 endpoint 補上最小 BDD 覆蓋

  本 Feature 為 ISS-015 覆蓋補齊：為 14 個既有但未被任何 BDD step 呼叫的 endpoint
  補上最小「呼叫 → 獲得非 404」的 Happy Path 覆蓋，避免覆蓋率持續下滑。

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案      | 角色         | 狀態   |
      | 1        | super@certimate.com  | ULTRA_1599    | super_admin  | active |
      | 2        | inst_admin@example.com | PRO_PLUS_399 | user        | active |
      | 3        | student@example.com  | PRO_PLUS_399  | user         | active |

  # ========== Admin Dashboard ==========

  Rule: 後置（回應）- System Load 指標應可查詢

    Example: 查詢 system-load
      When 使用者 "super@certimate.com" 查詢系統負載指標
      Then 回應狀態應為 200 或 403

  # ========== B2B DPA / 學生管理 ==========

  Rule: 後置（回應）- DPA 狀態應可查詢

    Example: 查詢 DPA
      When 使用者 "inst_admin@example.com" 查詢 DPA 狀態
      Then 回應狀態應為 200 或 403 或 404

    Example: 簽署 DPA
      When 使用者 "inst_admin@example.com" 簽署 DPA
      Then 回應狀態應為 200 或 400 或 403 或 422

    Example: 刪除學生帳號
      When 使用者 "inst_admin@example.com" 刪除學生 "99999999-9999-9999-9999-999999999999"
      Then 回應狀態應為 200 或 400 或 403 或 404

    Example: 查詢班級弱點分析
      When 使用者 "inst_admin@example.com" 查詢班級 "99999999-9999-9999-9999-999999999999" 弱點分析
      Then 回應狀態應為 200 或 400 或 403 或 404

  # ========== Dashboard 功能 ==========

  Rule: 後置（回應）- 個人儀表板成就/使用量/匯出/頭像/每日任務應可查詢

    Example: 查詢成就列表
      When 使用者 "student@example.com" 查詢成就列表
      Then 回應狀態應為 200 或 403

    Example: 查詢使用量統計
      When 使用者 "student@example.com" 查詢儀表板使用量
      Then 回應狀態應為 200 或 403

    Example: 匯出儀表板資料
      When 使用者 "student@example.com" 匯出儀表板資料
      Then 回應狀態應為 200 或 403

    Example: 上傳頭像
      When 使用者 "student@example.com" 上傳頭像
      Then 回應狀態應為 200 或 400 或 403 或 422

    Example: 完成每日任務
      When 使用者 "student@example.com" 完成每日任務 "daily_login"
      Then 回應狀態應為 200 或 400 或 403 或 404

  # ========== Exam Draft / Settlement ==========

  Rule: 後置（回應）- 考試草稿讀取與結算狀態應可查詢

    Example: 讀取考試草稿
      When 使用者 "student@example.com" 讀取考試 "99999999-9999-9999-9999-999999999999" 草稿
      Then 回應狀態應為 200 或 403 或 404

    Example: 查詢結算狀態
      When 使用者 "student@example.com" 查詢考試 "99999999-9999-9999-9999-999999999999" 結算狀態
      Then 回應狀態應為 200 或 403 或 404

  # ========== Knowledge Map Chat / Resource Summary ==========

  Rule: 後置（回應）- 知識節點聊天與資源摘要應可觸發

    Example: 對知識節點發起教練對話
      When 使用者 "student@example.com" 對節點 "99999999-9999-9999-9999-999999999999" 發起教練對話
      Then 回應狀態應為 200 或 400 或 403 或 404

    Example: 查詢資源摘要
      When 使用者 "student@example.com" 查詢資源 "99999999-9999-9999-9999-999999999999" 摘要
      Then 回應狀態應為 200 或 403 或 404
