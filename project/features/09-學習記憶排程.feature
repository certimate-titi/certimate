@frontend @command
Feature: 動態大腦精力調度排程

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email                | 訂閱方案      |
      | 1        | alice@example.com    | FREE          |
      | 2        | proplus@example.com  | PRO_PLUS_399  |
    And 使用者 "proplus@example.com" 的備考科目設定如下：
      | 科目     | 考試日期   | 自評程度     |
      | AWS SAA  | 2026-04-08 | intermediate |
      | PMP      | 2026-09-15 | beginner     |
    And 使用者 "proplus@example.com" 在 AWS SAA 科目的答題統計如下：
      | 題目 ID | 知識節點    | 成功次數 | 失敗次數 | Ease Factor | 下次複習日   |
      | 101     | S3 儲存服務 | 2        | 5        | 1.3         | 2026-03-24   |
      | 102     | IAM 管理   | 10       | 1        | 2.5         | 2026-04-10   |
      | 103     | EC2 運算   | 0        | 0        | 2.5         | null         |
      | 104     | VPC 網路   | 3        | 3        | 1.8         | 2026-03-26   |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 使用者必須至少有一個備考科目才能使用排程

    Example: 無備考科目的使用者查看排程建議失敗
      Given 使用者 "alice@example.com" 尚未設定任何備考科目
      When 使用者 "alice@example.com" 查看學習排程建議
      Then 操作失敗，錯誤為「請先在 Onboarding 或會員中心新增至少一個備考科目」

  Rule: 前置（參數）- 排程初始化必須有考試日期

    Example: 考試日期未設定時無法初始化排程
      Given 使用者 "proplus@example.com" 的 AWS SAA 考試日期為空
      When 系統嘗試為使用者 "proplus@example.com" 的 AWS SAA 科目初始化排程
      Then 操作失敗，錯誤為「必須設定考試日期才能初始化排程」

  # ========== 模式自動推導 ==========

  Rule: 後置（狀態）- 系統應根據距考日天數自動推導學習模式

    Example: 距考日 14 天內自動推導為 Sprint 模式
      Given 今日為 2026-04-01
      When 系統為使用者 "proplus@example.com" 的 AWS SAA 科目計算學習模式
      Then 學習模式應為 "sprint"
      And 模式推導依據應為「距考日 7 天，< 14 天」

    Example: 距考日 1 至 6 個月自動推導為 Standard 模式
      Given 使用者 "proplus@example.com" 的 PMP 考試日期為 2026-09-15
      And 今日為 2026-04-01
      When 系統為使用者 "proplus@example.com" 的 PMP 科目計算學習模式
      Then 學習模式應為 "standard"
      And 模式推導依據應為「距考日 167 天，介於 1-6 個月」

    Example: 距考日超過 6 個月自動推導為 Mastery 模式
      Given 使用者 "proplus@example.com" 的 PMP 考試日期為 2027-06-01
      And 今日為 2026-04-01
      When 系統為使用者 "proplus@example.com" 的 PMP 科目計算學習模式
      Then 學習模式應為 "mastery"

  # ========== Sprint 排題權重 ==========

  Rule: 後置（回應）- Sprint 模式排題應以錯題與生題為最高優先

    Example: Sprint 模式產出考卷中 70-80% 為弱項題目
      Given 使用者 "proplus@example.com" 的 AWS SAA 學習模式為 "sprint"
      When 系統為使用者 "proplus@example.com" 在 AWS SAA 科目產出 10 題模擬卷
      Then 模擬卷應包含 7 到 8 題來自以下類型：
        | 優先類型                      | 範例題目 |
        | Ease Factor < 1.5 的弱項題    | 101      |
        | 從未作答的生題                 | 103      |
      And 模擬卷不應包含 Ease Factor >= 2.5 且下次複習日遠於 7 天後的題目

  # ========== Standard 排題權重 ==========

  Rule: 後置（回應）- Standard 模式排題應遵循 SuperMemo-2 遺忘曲線

    Example: Standard 模式優先選取即將被遺忘的複習題
      Given 使用者 "proplus@example.com" 的 AWS SAA 學習模式為 "standard"
      And 今日為 2026-03-26
      When 系統為使用者 "proplus@example.com" 在 AWS SAA 科目產出 10 題模擬卷
      Then 模擬卷應優先包含下次複習日 <= 2026-03-26 的題目：
        | 題目 ID | 下次複習日  | 原因              |
        | 101     | 2026-03-24  | 已逾期 2 天       |
        | 104     | 2026-03-26  | 今日到期          |
      And 模擬卷不應包含題目 102（下次複習日 2026-04-10，尚未到期）

  # ========== Mastery 排題權重 ==========

  Rule: 後置（回應）- Mastery 模式排題應隨機探索知識盲區

    Example: Mastery 模式從全知識節點池隨機抽取
      Given 使用者 "proplus@example.com" 的 PMP 學習模式為 "mastery"
      When 系統為使用者 "proplus@example.com" 在 PMP 科目產出 10 題模擬卷
      Then 模擬卷應涵蓋至少 3 個不同的知識節點
      And 題目來源不受 Ease Factor 或下次複習日約束

  # ========== 考後統計更新 ==========

  Rule: 後置（狀態）- 提交考卷後系統應即時更新答題統計

    Example: 提交考卷後更新相關題目的統計資料
      Given 使用者 "proplus@example.com" 完成一份包含題目 101 與 104 的模擬卷
      And 題目 101 答對，題目 104 答錯
      When 使用者 "proplus@example.com" 提交考卷
      Then 題目 101 的統計應更新為：
        | 欄位         | 更新後值 |
        | success_count| 3        |
        | fail_count   | 5        |
      And 題目 104 的統計應更新為：
        | 欄位         | 更新後值 |
        | success_count| 3        |
        | fail_count   | 4        |
      And 兩題的 Ease Factor 與 next_review_date 應重新計算

    Example: FREE 用戶提交考卷後同樣享有統計更新
      Given 使用者 "alice@example.com" 完成一份模擬卷
      When 使用者 "alice@example.com" 提交考卷
      Then 系統應更新涉及題目的 success_count、fail_count 與 ease_factor

  # ========== 跨科目獨立 ==========

  Rule: 後置（狀態）- 各科目排程應獨立運作互不影響

    Example: 修改 AWS SAA 考試日期不影響 PMP 排程
      When 使用者 "proplus@example.com" 將 AWS SAA 考試日期從 2026-04-08 修改為 2026-04-01
      Then AWS SAA 的學習模式應重新計算
      And PMP 的學習模式應維持不變
