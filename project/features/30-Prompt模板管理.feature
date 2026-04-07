@ignore @command
Feature: Prompt 模板管理（僅 super_admin）

  # ============================================================
  # 本 Feature 涵蓋：
  # 1. Prompt 模板 CRUD（新增、查詢、更新、刪除）
  # 2. 版本管理（自動 version++、歷史查詢、版本回滾）
  # 3. A/B 測試（建立、流量分配、結束並選出勝者）
  # 4. Seed 同步（從檔案系統 seed 至 DB）
  # 5. AI 服務整合（Internal API、變數替換、Fallback）
  #
  # SSOT 來源：project/03_Research_and_Development/03_Prompt_Templates/
  # DB 表：prompt_templates_v2, prompt_template_versions, prompt_ab_tests
  # API 前綴：/api/v1/admin/prompt-templates
  # Internal API：/api/v1/internal/prompt-templates
  # ============================================================

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                   | 訂閱方案      | 角色         |
      | 1        | super@certimate.com     | ULTRA_1599    | super_admin  |
      | 2        | ops@certimate.com       | ULTRA_1599    | admin        |
      | 3        | user@certimate.com      | PRO_199       | user         |
    And 系統中有以下 Prompt 模板：
      | template_id | name           | display_name       | category | model         | max_tokens | temperature | current_version |
      | S-01        | safety_router  | 三維度安全分類      | safety   | gemini-flash  | 64         | 0.0         | 1               |
      | T-01        | coach_basic    | PRO_199 基礎教練    | teaching | gemini-flash  | 1024       | 0.7         | 1               |
      | T-02        | coach_advanced | PRO_PLUS_399 完整教練 | teaching | claude-3.5-sonnet | 2048 | 0.7         | 2               |

  # ========== 權限控制 ==========

  Rule: 前置（權限）- 僅 super_admin 可管理 Prompt 模板

    Example: 一般用戶無法存取 Prompt 模板管理 API
      When 使用者 "user@certimate.com" 查詢 Prompt 模板列表
      Then 操作失敗，錯誤為「權限不足」

    Example: admin 無法修改 Prompt 模板
      When 使用者 "ops@certimate.com" 更新 Prompt 模板 "S-01" 的 system_prompt 為 "new prompt"
      Then 操作失敗，錯誤為「權限不足」

  # ========== 模板列表與查詢 ==========

  Rule: 後置（回應）- 查詢模板列表應回傳所有模板摘要

    Example: super_admin 查詢所有模板
      When 使用者 "super@certimate.com" 查詢 Prompt 模板列表
      Then 操作成功
      And 回應應包含 3 筆模板
      And 每筆模板應包含：
        | 欄位            | 說明                  |
        | template_id     | 模板編號              |
        | name            | 英文識別名            |
        | display_name    | 中文顯示名            |
        | category        | 分類                  |
        | model           | 模型名稱              |
        | temperature     | 溫度參數              |
        | current_version | 當前版本號            |
        | is_active       | 是否啟用              |

    Example: super_admin 依分類篩選模板
      When 使用者 "super@certimate.com" 查詢 Prompt 模板列表，分類為 "teaching"
      Then 操作成功
      And 回應應包含 2 筆模板
      And 回應中所有模板的 category 應為 "teaching"

  Rule: 後置（回應）- 查詢單一模板應回傳完整內容含 prompt 文字

    Example: super_admin 查詢單一模板詳情
      When 使用者 "super@certimate.com" 查詢 Prompt 模板 "S-01" 詳情
      Then 操作成功
      And 回應應包含 system_prompt 欄位
      And 回應應包含 user_prompt 欄位
      And 回應應包含 variables 欄位

  # ========== 模板更新與版本管理 ==========

  Rule: 後置（狀態）- 更新模板應自動建立版本紀錄並遞增版本號

    Example: super_admin 更新 safety_router 的 system_prompt
      When 使用者 "super@certimate.com" 更新 Prompt 模板 "S-01"：
        | 欄位           | 值                                      |
        | system_prompt  | 你是安全分類器。回傳 JSON：{"relevant": bool} |
        | change_note    | 簡化為單維度分類                          |
      Then 操作成功
      And 模板 "S-01" 的 current_version 應為 2
      And 系統應記錄審計日誌：
        | 欄位     | 值                                    |
        | action   | update_prompt_template                |
        | details  | S-01 safety_router: v1 → v2           |

    Example: super_admin 調整 temperature 參數
      When 使用者 "super@certimate.com" 更新 Prompt 模板 "T-01"：
        | 欄位        | 值   |
        | temperature | 0.5  |
        | change_note | 降低教練語氣多樣性 |
      Then 操作成功
      And 模板 "T-01" 的 temperature 應為 0.5
      And 模板 "T-01" 的 current_version 應為 2

  Rule: 後置（回應）- 查詢版本歷史應回傳所有歷史版本（由新到舊）

    Example: super_admin 查詢 T-02 版本歷史
      When 使用者 "super@certimate.com" 查詢 Prompt 模板 "T-02" 的版本歷史
      Then 操作成功
      And 回應應包含 2 筆版本紀錄
      And 第一筆版本的 version 應為 2
      And 第二筆版本的 version 應為 1
      And 每筆版本應包含：
        | 欄位           | 說明           |
        | version        | 版本號         |
        | system_prompt  | 該版本的 prompt |
        | change_note    | 變更說明        |
        | created_by     | 修改者          |
        | created_at     | 修改時間        |

  Rule: 後置（狀態）- 回滾至指定版本應將該版本內容設為當前版本

    Example: super_admin 回滾 T-02 至版本 1
      When 使用者 "super@certimate.com" 將 Prompt 模板 "T-02" 回滾至版本 1
      Then 操作成功
      And 模板 "T-02" 的 current_version 應為 3
      And 模板 "T-02" 的 system_prompt 應與版本 1 的 system_prompt 相同
      And 系統應記錄審計日誌：
        | 欄位     | 值                                      |
        | action   | rollback_prompt_template                |
        | details  | T-02 coach_advanced: rollback to v1 → v3 |

      # 回滾不是覆蓋 — 是建立新版本（內容複製自目標版本），確保版本歷史完整不可變

  # ========== 模板新增 ==========

  Rule: 前置（參數）- 新增模板必須提供必要欄位

    Scenario Outline: 新增模板缺少 <缺少參數> 時失敗
      When 使用者 "super@certimate.com" 新增 Prompt 模板：
        | 欄位          | 值            |
        | template_id   | <template_id> |
        | name          | <name>        |
        | display_name  | <display_name>|
        | category      | <category>    |
        | model         | <model>       |
        | max_tokens    | <max_tokens>  |
        | system_prompt | <system_prompt>|
        | user_prompt   | <user_prompt> |
      Then 操作失敗，錯誤為「必要參數未提供」

      Examples:
        | 缺少參數       | template_id | name    | display_name | category | model        | max_tokens | system_prompt | user_prompt |
        | template_id    |             | test    | 測試模板      | safety   | gemini-flash | 256        | prompt        | user prompt |
        | system_prompt  | X-01        | test    | 測試模板      | safety   | gemini-flash | 256        |               | user prompt |

  Rule: 前置（唯一性）- template_id 與 name 不得重複

    Example: 新增重複 template_id 時失敗
      When 使用者 "super@certimate.com" 新增 Prompt 模板：
        | 欄位          | 值                |
        | template_id   | S-01              |
        | name          | new_safety        |
        | display_name  | 新安全分類         |
        | category      | safety            |
        | model         | gemini-flash      |
        | max_tokens    | 128               |
        | system_prompt | new system prompt |
        | user_prompt   | new user prompt   |
      Then 操作失敗，錯誤為「template_id 已存在」

  Rule: 後置（狀態）- 成功新增模板應自動建立版本 1

    Example: super_admin 新增自訂模板
      When 使用者 "super@certimate.com" 新增 Prompt 模板：
        | 欄位          | 值                      |
        | template_id   | F-03                    |
        | name          | study_tip               |
        | display_name  | 每日學習小撇步           |
        | category      | emotion                 |
        | model         | gemini-flash            |
        | max_tokens    | 128                     |
        | temperature   | 0.9                     |
        | system_prompt | 你是學習顧問，給出每日學習建議 |
        | user_prompt   | 學習狀態：{learning_state}   |
      Then 操作成功
      And 模板 "F-03" 的 current_version 應為 1
      And 模板 "F-03" 應有 1 筆版本歷史紀錄
      And 系統應記錄審計日誌：
        | 欄位     | 值                             |
        | action   | create_prompt_template         |
        | details  | F-03 study_tip (emotion)       |

  # ========== 模板停用 ==========

  Rule: 後置（狀態）- 停用模板不刪除資料，僅標記 is_active = false

    Example: super_admin 停用模板
      When 使用者 "super@certimate.com" 停用 Prompt 模板 "T-01"
      Then 操作成功
      And 模板 "T-01" 的 is_active 應為 false
      And 系統應記錄審計日誌：
        | 欄位     | 值                              |
        | action   | deactivate_prompt_template      |
        | details  | T-01 coach_basic                |

    Example: 停用中的模板不會被 AI 服務使用
      Given 模板 "T-01" 的 is_active 為 false
      When AI 服務請求模板 "coach_basic"
      Then 應回傳「模板已停用」錯誤

  # ========== A/B 測試 ==========

  Rule: 前置（唯一性）- 同一模板同時最多一個 running A/B 測試

    Example: 建立第二個 A/B 測試時失敗
      Given 模板 "T-01" 有一個 running 狀態的 A/B 測試
      When 使用者 "super@certimate.com" 為模板 "T-01" 建立 A/B 測試：
        | 欄位                   | 值                      |
        | name                   | 語氣對比測試 v2          |
        | variant_b_system_prompt| 你是嚴格的學習教練        |
        | variant_b_user_prompt  | {user_input}            |
        | traffic_split          | 30                      |
        | metric_name            | satisfaction             |
      Then 操作失敗，錯誤為「該模板已有進行中的 A/B 測試」

  Rule: 後置（狀態）- 建立 A/B 測試應記錄對照組版本

    Example: super_admin 建立教練語氣 A/B 測試
      When 使用者 "super@certimate.com" 為模板 "T-01" 建立 A/B 測試：
        | 欄位                   | 值                             |
        | name                   | 教練語氣對比測試                |
        | variant_b_system_prompt| 你是嚴格但專業的學習教練         |
        | variant_b_user_prompt  | {user_input}                   |
        | variant_b_temperature  | 0.5                            |
        | traffic_split          | 30                             |
        | metric_name            | accuracy                       |
      Then 操作成功
      And A/B 測試的 variant_a_version 應為模板 "T-01" 的 current_version
      And A/B 測試的 status 應為 "running"
      And 系統應記錄審計日誌：
        | 欄位     | 值                                      |
        | action   | create_ab_test                          |
        | details  | T-01 coach_basic: 教練語氣對比測試 (30%) |

  Rule: 後置（狀態）- AI 服務調用時根據 traffic_split 分配流量

    # 流量分配邏輯：
    # - 使用 user_id hash % 100 決定分組（確保同一用戶每次落在同一組）
    # - hash < traffic_split → variant B
    # - hash >= traffic_split → variant A（對照組）

    Example: A/B 測試中 AI 服務使用 variant A
      Given 模板 "T-01" 有一個 running A/B 測試，traffic_split 為 30
      When AI 服務為 user_id hash 值 50 的用戶請求模板 "coach_basic"
      Then 應使用 variant A（當前版本的 prompt）

    Example: A/B 測試中 AI 服務使用 variant B
      Given 模板 "T-01" 有一個 running A/B 測試，traffic_split 為 30
      When AI 服務為 user_id hash 值 20 的用戶請求模板 "coach_basic"
      Then 應使用 variant B 的 prompt

  Rule: 後置（狀態）- 結束 A/B 測試並選出勝者應自動套用

    Example: 選出 variant B 為勝者，自動建立新版本
      Given 模板 "T-01" 有一個 running A/B 測試 "test-1"
      When 使用者 "super@certimate.com" 結束 A/B 測試 "test-1"，勝者為 "B"
      Then 操作成功
      And A/B 測試 "test-1" 的 status 應為 "completed"
      And A/B 測試 "test-1" 的 winner 應為 "B"
      And 模板 "T-01" 的 system_prompt 應為 variant B 的 system_prompt
      And 模板 "T-01" 的 current_version 應遞增
      And 系統應記錄審計日誌：
        | 欄位     | 值                                               |
        | action   | complete_ab_test                                 |
        | details  | T-01 coach_basic: winner=B, applied as new version |

    Example: 選出 variant A 為勝者，不建立新版本
      Given 模板 "T-02" 有一個 running A/B 測試 "test-2"
      When 使用者 "super@certimate.com" 結束 A/B 測試 "test-2"，勝者為 "A"
      Then 操作成功
      And A/B 測試 "test-2" 的 status 應為 "completed"
      And A/B 測試 "test-2" 的 winner 應為 "A"
      And 模板 "T-02" 的 current_version 不應變動

    Example: 取消 A/B 測試
      Given 模板 "T-02" 有一個 running A/B 測試 "test-3"
      When 使用者 "super@certimate.com" 取消 A/B 測試 "test-3"
      Then 操作成功
      And A/B 測試 "test-3" 的 status 應為 "cancelled"

  # ========== Seed 同步 ==========

  Rule: 後置（狀態）- Seed 腳本應將檔案系統模板同步至 DB

    # seed 邏輯：
    # 1. 掃描 project/03_Prompt_Templates/ 下所有 .md 檔
    # 2. 解析 YAML frontmatter + prompt 內容
    # 3. DB 中不存在 → INSERT（建立模板 + 版本 1）
    # 4. DB 中已存在但檔案 version > DB version → UPDATE（建立新版本）
    # 5. DB 中已存在且版本相同 → SKIP

    Example: Seed 新模板至空 DB
      Given 資料庫中無任何 Prompt 模板
      And 檔案系統中有 17 個 Prompt 模板檔案
      When 執行 Prompt 模板 seed 腳本
      Then 資料庫中應有 17 筆 Prompt 模板
      And 每筆模板的 current_version 應為 1
      And 每筆模板應有 1 筆版本歷史紀錄

    Example: Seed 更新已存在的模板
      Given 資料庫中模板 "S-01" 的 current_version 為 1
      And 檔案系統中模板 "S-01" 的 version 為 2
      When 執行 Prompt 模板 seed 腳本
      Then 模板 "S-01" 的 current_version 應為 2
      And 模板 "S-01" 應有 2 筆版本歷史紀錄

    Example: Seed 跳過版本相同的模板
      Given 資料庫中模板 "S-01" 的 current_version 為 1
      And 檔案系統中模板 "S-01" 的 version 為 1
      When 執行 Prompt 模板 seed 腳本
      Then 模板 "S-01" 的 current_version 應維持為 1

  # ========== by-plan 模型支援 ==========

  Rule: 後置（狀態）- model=by-plan 的模板應支援分方案 max_tokens

    Example: 新增 by-plan 模板
      When 使用者 "super@certimate.com" 新增 Prompt 模板：
        | 欄位              | 值                                                          |
        | template_id       | T-05                                                        |
        | name              | custom_coach                                                |
        | display_name      | 自訂教練                                                     |
        | category          | teaching                                                    |
        | model             | by-plan                                                     |
        | max_tokens        | 1024                                                        |
        | max_tokens_by_plan| {"PRO_199":1024,"PRO_PLUS_399":2048,"ULTRA_1599":4096}      |
        | system_prompt     | 你是學習教練                                                 |
        | user_prompt       | {user_input}                                                |
      Then 操作成功
      And 模板 "T-05" 的 model 應為 "by-plan"
      And 模板 "T-05" 的 max_tokens_by_plan 應包含 PRO_199、PRO_PLUS_399、ULTRA_1599

  # ========== AI 服務整合 ==========

  Rule: 後置（回應）- Internal API 應依 name 回傳生效中 prompt（無需 auth）

    Example: Internal API 依 name 取得啟用中模板
      When Internal API 請求模板 "safety_router"
      Then 操作成功
      And 回應應包含 system_prompt 欄位
      And 回應應包含 user_prompt 欄位
      And 回應應包含 model 欄位
      And 回應應包含 max_tokens 欄位
      And 回應應包含 temperature 欄位

    Example: Internal API 請求不存在的模板應回傳 404
      When Internal API 請求模板 "nonexistent_template"
      Then 操作失敗，錯誤為「模板不存在」

  Rule: 後置（回應）- Prompt 模板的變數佔位符應可被 render_prompt 正確替換

    # render_prompt 邏輯：
    # 模板中的 {var_name} 佔位符會被替換為實際值
    # 例如：system_prompt 中的 {subject_name} → "AWS SAA"

    Example: render_prompt 正確替換佔位符
      Given 一段 prompt 模板內容為 "你正在學習 {subject_name}，請回答 {user_input}"
      When 使用變數 subject_name="AWS SAA"、user_input="什麼是 EC2？" 進行替換
      Then 替換結果應為 "你正在學習 AWS SAA，請回答 什麼是 EC2？"
      And 替換結果不應包含 "{subject_name}"
      And 替換結果不應包含 "{user_input}"

  Rule: 後置（狀態）- AI 服務讀取模板失敗時應 fallback 至 hardcoded prompt

    # fallback 邏輯：
    # 1. AI 服務呼叫 get_prompt_for_ai(name) 取得 DB 模板
    # 2. 若模板不存在 → 回傳 error
    # 3. 呼叫端使用 hardcoded prompt 作為 fallback
    # 4. 系統繼續正常運作，不影響使用者體驗

    Example: 模板不存在時 get_prompt_for_ai 回傳錯誤
      Given 資料庫中無任何 Prompt 模板
      When 以 service 查詢模板 "stage2_question_generation"
      Then service 應回傳 error 且 status_code 為 404

  # ========== API 端點摘要 ==========

  # | 方法   | 路徑                                              | 說明              |
  # |--------|--------------------------------------------------|-------------------|
  # | GET    | /api/v1/admin/prompt-templates                    | 列表（支援 ?category= 篩選）|
  # | GET    | /api/v1/admin/prompt-templates/{template_id}      | 單一模板詳情       |
  # | POST   | /api/v1/admin/prompt-templates                    | 新增模板           |
  # | PATCH  | /api/v1/admin/prompt-templates/{template_id}      | 更新模板（自動版本++）|
  # | DELETE | /api/v1/admin/prompt-templates/{template_id}      | 停用模板（軟刪除）  |
  # | GET    | /api/v1/admin/prompt-templates/{template_id}/versions | 版本歷史       |
  # | POST   | /api/v1/admin/prompt-templates/{template_id}/rollback | 回滾至指定版本 |
  # | POST   | /api/v1/admin/prompt-templates/{template_id}/ab-tests | 建立 A/B 測試  |
  # | PATCH  | /api/v1/admin/prompt-templates/ab-tests/{test_id}     | 結束/取消 A/B 測試 |
  # | GET    | /api/v1/admin/prompt-templates/ab-tests            | 列出所有 A/B 測試  |
  #
  # 內部 API（非 admin，供 AI 服務調用）：
  # | GET    | /api/v1/internal/prompt-templates/{name}           | 依 name 取得生效中 prompt（含 A/B 分流）|
