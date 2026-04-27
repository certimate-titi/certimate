@backend
Feature: 測驗結果

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | FREE     |
      | 2        | bob@example.com    | PRO_199  |
    And 系統中有以下歷史測驗記錄：
      | 測驗 ID | 使用者 ID | 狀態      | 答對數 | 總題數 | 得分 | 合格分數 | 提交時間            |
      | 1       | 1        | SUBMITTED | 60     | 100    | 60   | 72       | 2024-01-10 10:00:00 |
      | 2       | 1        | SUBMITTED | 80     | 100    | 80   | 72       | 2024-01-15 14:00:00 |
      | 3       | 2        | SUBMITTED | 55     | 65     | 85   | 80       | 2024-01-12 09:00:00 |
    And 測驗 2 包含以下知識節點答對率：
      | 節點名稱 | 答對數 | 出題數 | 答對率 |
      | EC2 運算 | 8      | 10     | 80%    |
      | IAM 身分 | 4      | 10     | 40%    |
      | S3 儲存  | 8      | 10     | 80%    |
      | VPC 網路 | 5      | 10     | 50%    |

  # ========== 前置條件 ==========

  Rule: 前置（狀態）- 只能查看自己的測驗結果

    Example: 查看其他使用者的測驗結果失敗
      When 使用者 "alice@example.com" 查看測驗 3 的結果
      Then 操作失敗
      And 錯誤訊息應為 "無存取此測驗結果的權限"

  Rule: 前置（狀態）- 只能查看已提交狀態的測驗結果

    Example: 查看進行中測驗的結果失敗
      Given 系統中有以下測驗：
        | 測驗 ID | 使用者 ID | 狀態        | 總題數 | 考試時長（分鐘） |
        | 10      | 1        | IN_PROGRESS | 10     | 30              |
      When 使用者 "alice@example.com" 查看測驗 10 的結果
      Then 操作失敗
      And 錯誤訊息應為 "測驗尚未提交，無法查看結果"

  # ========== 後置條件 ==========

  Rule: 後置（回應）- 結果頁應回傳得分、合格與否判斷、合格門檻及與上次測驗的比較

    Example: 查看通過合格分數的測驗結果
      When 使用者 "alice@example.com" 查看測驗 2 的結果
      Then 操作成功
      And 結果應包含：
        | 欄位       | 值         |
        | 得分       | 80         |
        | 合格狀態   | 通過       |
        | 合格分數   | 72         |
        | 與上次比較 | +20 分進步 |

    Example: 查看未達合格分數的測驗結果（鼓勵性文案）
      When 使用者 "alice@example.com" 查看測驗 1 的結果
      Then 操作成功
      And 結果應包含：
        | 欄位     | 值       |
        | 得分     | 60       |
        | 合格狀態 | 未達門檻 |
        | 合格分數 | 72       |

  Rule: 後置（回應）- 結果頁應回傳各知識節點答對率並依閾值標示顏色

    Example: 查看測驗結果時取得知識節點答對率分析
      When 使用者 "alice@example.com" 查看測驗 2 的知識點分析
      Then 操作成功
      And 知識點分析應包含：
        | 節點名稱 | 答對率 | 顏色標示 |
        | EC2 運算 | 80%    | 綠色     |
        | IAM 身分 | 40%    | 紅色     |
        | S3 儲存  | 80%    | 綠色     |
        | VPC 網路 | 50%    | 紅色     |

    Example: 答對率低於 60% 的節點應標示紅色警戒
      When 使用者 "alice@example.com" 查看測驗 2 的知識點分析
      Then 節點 "IAM 身分" 的顏色標示應為 "紅色"
      And 節點 "VPC 網路" 的顏色標示應為 "紅色"

    Example: 答對率高於 80% 的節點應標示綠色安全
      When 使用者 "alice@example.com" 查看測驗 2 的知識點分析
      Then 節點 "EC2 運算" 的顏色標示應為 "綠色"

  Rule: 後置（回應）- 測驗結果頁應根據成績走向觸發不同的情感化互動與 AI 總評

    Example: 成績進步時觸發慶祝動畫與稱讚
      Given 使用者 "bob@example.com" 的上次測驗得分為 75，本次測驗 3 得分為 85
      When 使用者 "bob@example.com" 查看測驗 3 的結果
      Then 畫面應觸發撒花動畫 (Confetti)

    Example: FREE 用戶查看測驗結果時不包含 AI 考後總評
      When 使用者 "alice@example.com" 查看測驗 2 的結果
      Then 操作成功

  Rule: 後置（回應）- 支援產生與分享個人化成績卡片 (Score Card)

    Example: 測驗結果可產生包含品牌浮水印與鼓勵文案的個人成績卡片
      When 使用者 "alice@example.com" 查看測驗 2 的結果
      Then 系統應提供「產生與分享成績卡片」的功能按鈕

  Rule: 後置（狀態）- 測驗結果頁面應顯示免責聲明

    Example: 確保使用者了解成績不保證真實考試通過率
      When 使用者 "alice@example.com" 查看測驗 2 的結果
      Then 畫面底部應顯示提示文字 "本模擬考試結果僅反映當前熟悉度"

  # ========== UI 元件補充場景 ==========

  Rule: 後置（回應）- 分享到 LinkedIn 按鈕應顯示為 placeholder 未實作狀態

    Example: 點擊分享到 LinkedIn 按鈕顯示即將推出提示
      When 使用者 "alice@example.com" 查看測驗 2 的結果
      And 使用者 "alice@example.com" 點擊分享到 LinkedIn 按鈕
      Then 畫面應顯示提示訊息 "LinkedIn 分享功能即將推出，敬請期待"

  Rule: 後置（回應）- 下載成績卡片按鈕應顯示為 placeholder 未實作狀態

    Example: 點擊下載成績卡片按鈕顯示即將推出提示
      When 使用者 "alice@example.com" 查看測驗 2 的結果
      And 使用者 "alice@example.com" 點擊下載成績卡片按鈕
      Then 畫面應顯示提示訊息 "成績卡片下載功能即將推出，敬請期待"

  Rule: 後置（回應）- AI 教練介入卡片應可導航至錯題複習頁面

    Example: 點擊 AI 教練介入卡片導航至錯題複習
      Given 使用者 "bob@example.com" 查看測驗 3 的結果
      And 測驗 3 的知識點分析中存在答對率低於 60% 的節點
      When 使用者 "bob@example.com" 點擊 AI 教練介入卡片上的「前往錯題複習」按鈕
      Then 頁面應導航至錯題複習頁面
      And 錯題複習頁面應自動帶入測驗 3 的錯題範圍

  Rule: 後置（回應）- 領域分析進度條應顯示各知識節點的正確百分比

    Example: 領域分析區塊顯示各節點進度條與正確百分比
      When 使用者 "alice@example.com" 查看測驗 2 的知識點分析
      Then 操作成功
      And 領域分析區塊應以進度條呈現以下節點正確百分比：
        | 節點名稱 | 進度條百分比 | 顏色標示 |
        | EC2 運算 | 80%          | 綠色     |
        | IAM 身分 | 40%          | 紅色     |
        | S3 儲存  | 80%          | 綠色     |
        | VPC 網路 | 50%          | 紅色     |

  # ========== 知識圖譜進度變化 ==========

  # ForceGraph 視覺化為純前端元件，已移至 project/features/06-測驗結果.feature
  # （弱點分析 API 仍由 backend 驗，已涵蓋於上方 Rules）
