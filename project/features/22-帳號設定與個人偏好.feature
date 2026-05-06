@frontend @command
Feature: 帳號設定與個人偏好

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案   | 角色  |
      | 1        | user@example.com   | PRO_199    | USER  |
    And 使用者 "user@example.com" 已完成引導流程

  # ========== 個人資料管理 ==========

  Rule: 命令（修改）- 使用者可更新個人檔案

    Example: 成功更新個人資料
      When 使用者 "user@example.com" 更新個人資料：
        | 欄位               | 值              |
        | display_name       | 王小明           |
        | age                | 28              |
        | education          | 大學             |
        | occupation         | 軟體工程師        |
        | daily_study_minutes| 60              |
        | learning_style     | visual          |
      Then 操作應成功
      And API 回應應包含更新後的個人資料

    Example: 顯示名稱不可為空
      When 使用者 "user@example.com" 更新個人資料：
        | 欄位           | 值  |
        | display_name   |     |
      Then 操作應失敗，錯誤訊息為 "顯示名稱不可為空"

  # ========== 密碼變更 ==========

  Rule: 命令（安全）- 使用者可變更密碼

    Example: 成功變更密碼
      When 使用者 "user@example.com" 變更密碼：
        | 欄位              | 值            |
        | current_password  | old_pass123   |
        | new_password      | new_pass456   |
      Then 操作應成功

    Example: 舊密碼不正確時應失敗
      When 使用者 "user@example.com" 變更密碼：
        | 欄位              | 值            |
        | current_password  | wrong_pass    |
        | new_password      | new_pass456   |
      Then 操作應失敗，錯誤訊息為 "目前密碼不正確"

  # ========== 使用量查詢 ==========

  Rule: 查詢 - 使用者可查看本月使用量

    Example: 查詢使用量摘要
      When 使用者 "user@example.com" 查詢使用量
      Then 操作應成功
      And API 回應應包含：
        | 欄位                 |
        | exams_used           |
        | exams_limit          |
        | documents_used       |
        | documents_limit      |

  # ========== 帳號刪除 ==========

  Rule: 命令（危險）- 使用者可申請刪除帳號

    Example: 確認刪除帳號
      When 使用者 "user@example.com" 申請刪除帳號並輸入確認文字 "刪除我的帳號"
      Then 操作應成功
      And 使用者帳號狀態應變更為 "DELETED"

    Example: 確認文字不符時應拒絕
      When 使用者 "user@example.com" 申請刪除帳號並輸入確認文字 "不要刪除"
      Then 操作應失敗，錯誤訊息為 "確認文字不符"

  # ========== 通知偏好 ==========

  Rule: 命令（偏好）- 使用者可設定通知偏好

    Example: 更新通知偏好設定
      When 使用者 "user@example.com" 更新通知偏好：
        | 欄位                | 值    |
        | daily_reminder      | true  |
        | pre_exam_reminder   | true  |
        | weekly_report       | false |
      Then 操作應成功

  # ========== 個人資料個人化 AI（2026-05 新增）==========

  @backend
  Rule: 後置（個人化）- 使用者填寫的年齡 / 學歷 / 職業應自動帶入 AI prompt 模板

    Example: 個人資料齊全時 5 個教學鼓勵類模板均接收個人化背景
      Given 使用者 "ultra@example.com" 的個人資料為：
        | 欄位     | 值         |
        | 年齡     | 32         |
        | 最高學歷 | 碩士       |
        | 職業     | 軟體工程師 |
      When 系統呼叫下列任一 prompt 模板：F-01 encouragement / F-02 weekly_report / T-02 coach_advanced / T-03 wrong_answer_analysis / T-04 post_exam_summary
      Then 渲染後的 system_prompt 應包含 "使用者背景：32 歲、碩士學歷、軟體工程師"
      And age / education / career 變數應分別注入為 "32" / "碩士" / "軟體工程師"

    Example: 個人資料部分缺失時自動省略缺失欄位
      Given 使用者 "pro@example.com" 的個人資料為：
        | 欄位     | 值     |
        | 年齡     | 22     |
        | 最高學歷 | （空） |
        | 職業     | （空） |
      When 系統呼叫 T-02 coach_advanced 模板渲染
      Then 渲染後 user_background_instruction 應為 "使用者背景：22 歲。請依此調整講解深度與用詞。"
      And 不應出現「未提供」等佔位字

    Example: 個人資料全部空白時 user_background_instruction 為空字串
      Given 使用者 "free@example.com" 的個人資料中年齡 / 學歷 / 職業皆為空
      When 系統呼叫任一個人化 AI 模板渲染
      Then 渲染後 user_background_instruction 應為空字串

    Example: 出題類模板（E-01/E-02/E-03/E-05/E-06/E-07）不應接收個人化參數
      When 系統呼叫考題生成 / 知識樹合併 / 考綱逆向工程等模板
      Then 渲染變數中不應包含 age / education / career
      And 此舉確保題目客觀性，避免依使用者背景產生不公平差異
