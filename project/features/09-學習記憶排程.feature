@ignore
Feature: 動態大腦精力調度排程 (Sprint / Standard / Mastery)

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 2        | proplus@example.com| PRO_PLUS |
    And 系統擁有針對該使用者的測驗題目歷程資料庫：
      | 題目 ID | Success Count | Fail Count | Ease Factor |
      | 101     | 2             | 5          | 1.3         |
      | 102     | 10            | 1          | 2.5         |
      | 103     | 0             | 0          | 2.5         |

  # ========== 排程與動態權重演算法 ==========

  Rule: 後置（演算法參數）- 排題模組必須支援三種基於時間軸的動態學習模式

    Example: 使用 Sprint (短期衝刺) 模式產生爆肝考卷
      When 使用者 "proplus@example.com" 選擇 "Sprint 衝刺模式"，設定距離期末考僅有 3 天
      Then 排題演算法應拋棄常規的艾賓浩斯間隔，全面套用高強度的 Sprint 壓縮權重
      And 產出的隨機模擬卷中，應有最高占比 (約 70~80%) 鎖定 `Ease Factor < 1.5` 或 `Fail Count` 異常的錯題與「從未遇到的生肉題」 
      And 演算法將毅然放棄已經冷藏在長期記憶區（遺忘邊緣的舊題），不浪費運算算力與學生的緊急時間考這種題型

    Example: 使用 Standard (正常準備) 模式產生規律考卷
      When 使用者 "proplus@example.com" 選擇 "Standard 備考模式"，距離大考 30 天以上
      Then 排題演算法應切換權重，嚴格遵循 SuperMemo-2 等科學化遺忘曲線之天數間隔參數
      And 在隨機 50 題的配置中，應以「剛好準備被大腦遺忘的複習題」占據最精華比例

    Example: 使用 Mastery (長久學習) 模式探勘知識框架
      When 使用者 "proplus@example.com" 在非考試期間選擇 "Mastery 培養模式"
      Then 排題演算法應完全放任其 AI 代理人在廣大知識節點池中隨機漫遊，或運用 Temperature 放大的變形出題法
      And 目標不再以提分為主，而是協助學生找出長年未碰觸的知識死角

  # ========== 雙重漏斗篩選與引擎高頻寫入 ==========

  Rule: 後置（狀態同步）- 用戶送出答卷時的 DB 高耗能更新作業
    
    Example: 用戶答完題後立即更新屬性與心智圖節點的統計資料
      When 使用者提交模擬測驗卷的答案送出結算
      Then 系統應在背景快速更新此回涉及的所有紀錄之 `Success Count`、`Fail Count` 以及即時校正新的 `Ease Factor`
      And 即便是免費用戶也照常享受此高頻寫入權益，確保全平台學習歷史與成就系統的一致性
