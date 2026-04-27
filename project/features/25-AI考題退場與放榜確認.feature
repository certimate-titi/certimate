@frontend
Feature: AI 考題退場與放榜確認 (AI Question Retirement & Exam Result Confirmation)

  Background:
    Given 系統中有以下使用者帳號：
      | 使用者 ID | Email              | 訂閱方案 |
      | 1        | alice@example.com  | PRO_199  |
      | 2        | bob@example.com    | FREE     |
    And 系統中有以下備考科目：
      | 科目 ID | 科目名稱       |
      | S1      | 證券商業務員   |
      | S2      | 期貨商業務員   |
    And 使用者 "alice@example.com" 有學習歷程於科目 "證券商業務員"：
      | 欄位          | 值           |
      | exam_date     | 2026-05-15   |
      | result_date   | 2026-06-01   |

  # ==========================================================================
  # 一、AI 考題來源標記
  # ==========================================================================

  Rule: 前置（狀態）- AI 生成的考題必須標記 source_type 為 ai_generated

    Example: AI 生成考題自動標記為 ai_generated
      Given 使用者 "alice@example.com" 對科目 "證券商業務員" 發起 AI 出題
      When AI 出題服務生成 10 題選擇題
      Then 所有生成的題目 source_type 應為 "ai_generated"
      And 所有生成的題目 quality_flag 應為 "review"
      And 所有生成的題目 expires_at 應為生成時間加 7 天

    Example: 考古題匯入時 source_type 標記為 historical
      Given 管理員匯入一批考古題至科目 "證券商業務員"
      When 匯入完成
      Then 所有匯入的題目 source_type 應為 "historical"
      And 所有匯入的題目 expires_at 應為 NULL

  # ==========================================================================
  # 二、AI 考題品質閘門
  # ==========================================================================

  Rule: 前置（參數）- AI 生成的題目必須通過品質閘門才能入庫

    Example: AI 生成的題目通過品質閘門後升級為 ok
      Given AI 出題服務生成以下題目：
        | 題幹            | 選項A      | 選項B      | 選項C      | 選項D      | 正確答案 |
        | 何謂融資融券？   | 信用交易   | 現貨交易   | 期貨交易   | 選擇權交易 | A        |
      When 系統執行品質閘門檢查
      Then 該題目 quality_flag 應升級為 "ok"

    Example: 選項不足 4 個的 AI 題不入庫
      Given AI 出題服務生成以下題目：
        | 題幹            | 選項A      | 選項B      | 選項C      | 選項D | 正確答案 |
        | 何謂融資融券？   | 信用交易   | 現貨交易   |            |       | A        |
      When 系統執行品質閘門檢查
      Then 該題目應被丟棄，不入庫
      And 丟棄原因應為 "選項不足 4 個"

    Example: 題幹過短的 AI 題不入庫
      Given AI 出題服務生成以下題目：
        | 題幹   | 選項A | 選項B | 選項C | 選項D | 正確答案 |
        | 何謂？ | A     | B     | C     | D     | A        |
      When 系統執行品質閘門檢查
      Then 該題目應被丟棄，不入庫
      And 丟棄原因應為 "題幹長度不足 10 字"

  # ==========================================================================
  # 三、AI 考題退場條件（學習價值歸零）
  # ==========================================================================

  Rule: 後置（狀態）- 未作答的 AI 題在 7 天後退場

    Example: AI 題生成後 7 天未作答則自動軟刪除
      Given 使用者 "alice@example.com" 於 7 天前生成了 5 題 AI 題
      And 這些 AI 題從未被作答
      When 系統執行每日退場掃描
      Then 這 5 題 AI 題的 retired_at 應被設定為當前時間
      And retention_reason 應為 "未作答逾期"

  Rule: 後置（狀態）- 答對且無後續互動的 AI 題在 30 天後退場

    Example: 答對的 AI 題 30 天後無互動則軟刪除
      Given 使用者 "alice@example.com" 於 30 天前答對了一題 AI 題
      And 該題未加入錯題本、未被收藏、未標記為危險盲點
      When 系統執行每日退場掃描
      Then 該題的 retired_at 應被設定為當前時間
      And retention_reason 應為 "答對無後續互動"

  Rule: 後置（狀態）- 在錯題本中的 AI 題需 SM-2 五階段全通過後才可退場

    Example: SM-2 排程進行中的 AI 題不退場
      Given 使用者 "alice@example.com" 有一題 AI 題在錯題本中
      And 該題 SM-2 排程目前為第 3 階段
      And 該題 expires_at 已過期
      When 系統執行每日退場掃描
      Then 該題不應被退場
      And retention_reason 應更新為 "SM-2 排程進行中（第 3 階段）"

    Example: SM-2 五階段全通過的 AI 題 14 天後退場
      Given 使用者 "alice@example.com" 有一題 AI 題在錯題本中
      And 該題 SM-2 五階段已全部通過，完成日為 14 天前
      When 系統執行每日退場掃描
      Then 該題的 retired_at 應被設定為當前時間
      And retention_reason 應為 "SM-2 五階段完成"

  Rule: 後置（狀態）- 危險盲點（確定+答錯）的 AI 題需修正後額外保留

    Example: 危險盲點 AI 題修正後連續 3 次答對才可退場
      Given 使用者 "alice@example.com" 有一題 AI 題標記為危險盲點
      And 該題修正後已連續 3 次「確定+答對」
      And 最後一次答對日為 14 天前
      When 系統執行每日退場掃描
      Then 該題的 retired_at 應被設定為當前時間
      And retention_reason 應為 "危險盲點已修正"

    Example: 危險盲點 AI 題未修正時不退場
      Given 使用者 "alice@example.com" 有一題 AI 題標記為危險盲點
      And 該題尚未連續 3 次「確定+答對」
      When 系統執行每日退場掃描
      Then 該題不應被退場

  Rule: 後置（狀態）- 知識節點掌握度影響 AI 題退場

    Example: 知識節點仍為紅燈時相關 AI 題不退場
      Given 使用者 "alice@example.com" 有 AI 題對應知識節點 "證券交易法規"
      And 該知識節點掌握度為 🔴（< 60%）
      And 該 AI 題 expires_at 已過期
      When 系統執行每日退場掃描
      Then 該題不應被退場
      And retention_reason 應更新為 "對應知識節點未達精熟"

    Example: 知識節點轉為綠燈後 14 天 AI 題退場
      Given 使用者 "alice@example.com" 有 AI 題對應知識節點 "證券交易法規"
      And 該知識節點於 14 天前轉為 🟢（≥ 80%）
      And 該節點下所有 AI 題 SM-2 皆達第 4 階段以上
      When 系統執行每日退場掃描
      Then 該節點下的 AI 題 retired_at 應被設定為當前時間
      And retention_reason 應為 "知識節點已精熟"

  Rule: 後置（狀態）- 長期未作答的 AI 題依閒置規則退場

    Example: 超過 60 天未互動的 AI 題退場
      Given 使用者 "alice@example.com" 有一題 AI 題
      And 該題最後互動時間為 60 天前
      When 系統執行每日退場掃描
      Then 該題的 retired_at 應被設定為當前時間
      And retention_reason 應為 "長期閒置"

  Rule: 後置（狀態）- 用戶收藏的 AI 題不自動退場

    Example: 已收藏的 AI 題即使過期也不退場
      Given 使用者 "alice@example.com" 有一題 AI 題已收藏
      And 該題 expires_at 已過期
      When 系統執行每日退場掃描
      Then 該題不應被退場
      And retention_reason 應為 "用戶收藏"

  # ==========================================================================
  # 四、AI 考題品質退場
  # ==========================================================================

  Rule: 後置（狀態）- 品質不合格的 AI 題立即退場

    Example: 被回報 3 次以上的 AI 題立即退場
      Given 一題 AI 題被 3 位不同使用者回報品質問題
      When 系統偵測到回報次數達標
      Then 該題的 retired_at 應被立即設定
      And retention_reason 應為 "品質不合格"
      And quality_flag 應更新為 "low"

  # ==========================================================================
  # 五、軟刪除與硬刪除
  # ==========================================================================

  Rule: 後置（狀態）- 軟刪除的 AI 題在 90 天後硬刪除

    Example: 軟刪除 90 天後資料完全清除
      Given 一題 AI 題於 90 天前被軟刪除（retired_at 已設定）
      When 系統執行每日硬刪除掃描
      Then 該題應從資料庫中永久刪除
      And 相關的 JSON 存檔應一併刪除
      And 該題資料不可恢復

    Example: 軟刪除未滿 90 天的 AI 題可被恢復
      Given 一題 AI 題於 30 天前被軟刪除
      And 使用者 "alice@example.com" 選擇「再次報考」同科目
      When 系統恢復該科目的軟刪除 AI 題
      Then 該題的 retired_at 應被清除
      And expires_at 應重新計算

  # ==========================================================================
  # 六、available_questions 計數隔離
  # ==========================================================================

  Rule: 後置（回應）- 科目題庫數量僅計算考古題

    Example: available_questions 不包含 AI 生成題目
      Given 科目 "證券商業務員" 有 760 題考古題和 50 題 AI 生成題
      When 系統計算 available_questions
      Then 科目 "證券商業務員" 的 available_questions 應為 760

  # ==========================================================================
  # 七、放榜日期設定
  # ==========================================================================

  Rule: 命令（設定）- 使用者可為備考科目設定放榜日期

    Example: 在 Onboarding Step 2 設定放榜日期
      Given 使用者 "bob@example.com" 進入 Step 2 選擇備考科目
      When 使用者選擇以下備考科目並設定：
        | 科目         | 預計考試日期 | 預計放榜日期 | 自評程度 |
        | 證券商業務員 | 2026-05-15  | 2026-06-01  | 初學     |
      Then 已選科目列表應顯示考試日期與放榜日期

    Example: 在帳號設定頁補填或修改放榜日期
      Given 使用者 "alice@example.com" 有學習歷程於科目 "證券商業務員"
      When 使用者修改放榜日期為 "2026-06-05"
      Then 操作成功
      And 學習歷程的 result_date 應更新為 "2026-06-05"

  # ==========================================================================
  # 八、放榜推送通知
  # ==========================================================================

  Rule: 後置（事件）- 放榜日當天系統推送確認通知

    Example: 放榜日推送考試結果確認通知
      Given 使用者 "alice@example.com" 的科目 "證券商業務員" 放榜日為今天
      When 系統執行放榜日推送排程
      Then 系統應發送推送通知給使用者 "alice@example.com"
      And 通知內容應詢問是否考取
      And 通知應包含「確認考取」和「未考取」兩個按鈕

    Example: 放榜日+3天未回覆發送提醒
      Given 使用者 "alice@example.com" 的放榜通知已發送 3 天
      And 使用者尚未回覆放榜結果
      When 系統執行提醒排程
      Then 系統應發送第二次提醒通知

    Example: 放榜日+7天未回覆預設為未考取
      Given 使用者 "alice@example.com" 的放榜通知已發送 7 天
      And 使用者尚未回覆放榜結果
      When 系統執行預設處理排程
      Then 學習歷程的 exam_result_status 應自動設為 "failed"
      And 系統應發送通知告知資料將保留 30 天
      And data_expiry_date 應設為今天加 30 天

  # ==========================================================================
  # 九、考取流程
  # ==========================================================================

  Rule: 命令（確認考取）- 考取後祝賀並啟動 7 天刪除倒數

    Example: 使用者確認考取
      When 使用者 "alice@example.com" 確認科目 "證券商業務員" 考試結果為「考取」
      Then 操作成功
      And 學習歷程的 exam_result_status 應為 "passed"
      And data_expiry_date 應設為今天加 7 天
      And 系統應發送祝賀通知
      And 通知內容應包含「資料將保留 7 天」的提示

    Example: 考取確認後 7 天自動刪除該科目 AI 題
      Given 使用者 "alice@example.com" 於 7 天前確認考取科目 "證券商業務員"
      When 系統執行放榜後退場掃描
      Then 該科目下所有 AI 生成題目應被軟刪除
      And retention_reason 應為 "考取後資料清除"

  Rule: 後置（事件）- 考取後第 3 天推薦下一張證照

    Example: 考取後交叉推薦相關證照
      Given 使用者 "alice@example.com" 於 3 天前確認考取科目 "證券商業務員"
      When 系統執行交叉推薦排程
      Then 系統應發送推薦通知
      And 通知內容應包含同領域的進階證照選項

  # ==========================================================================
  # 十、未考取流程
  # ==========================================================================

  Rule: 命令（確認未考取）- 未考取後鼓勵並詢問是否再報考

    Example: 使用者確認未考取
      When 使用者 "alice@example.com" 確認科目 "證券商業務員" 考試結果為「未考取」
      Then 操作成功
      And 學習歷程的 exam_result_status 應為 "failed"
      And 系統應發送鼓勵通知
      And 通知內容應詢問是否再次報考

    Example: 未考取後選擇再次報考
      Given 使用者 "alice@example.com" 確認科目 "證券商業務員" 未考取
      When 使用者選擇「再次報考」並設定：
        | 欄位              | 值          |
        | 新考試日期        | 2026-08-15  |
        | 新放榜日期        | 2026-09-01  |
      Then 操作成功
      And 學習歷程的 exam_result_status 應更新為 "retake"
      And exam_date 應更新為 "2026-08-15"
      And result_date 應更新為 "2026-09-01"
      And data_expiry_date 應清除
      And 系統應根據弱點分析重新規劃學習計畫
      And 軟刪除中的 AI 題應恢復（若在 90 天內）

    Example: 未考取後選擇不再報考
      Given 使用者 "alice@example.com" 確認科目 "證券商業務員" 未考取
      When 使用者選擇「不再報考」
      Then 操作成功
      And data_expiry_date 應設為今天加 30 天
      And 系統應發送溫暖告別通知
      And 通知內容應包含「資料將保留 30 天」的提示

    Example: 不再報考確認後 30 天自動刪除該科目 AI 題
      Given 使用者 "alice@example.com" 於 30 天前確認不再報考科目 "證券商業務員"
      When 系統執行放榜後退場掃描
      Then 該科目下所有 AI 生成題目應被軟刪除
      And retention_reason 應為 "不再報考後資料清除"

  # ==========================================================================
  # 十一、AI 出題功能條款同意
  # ==========================================================================

  Rule: 前置（參數）- 首次使用 AI 出題須同意退場條款

    Example: 首次使用 AI 出題時顯示條款同意彈窗
      Given 使用者 "bob@example.com" 從未使用過 AI 出題功能
      When 使用者發起 AI 出題
      Then 系統應顯示 AI 出題功能說明與條款同意彈窗
      And 彈窗應說明 AI 題為臨時性學習素材
      And 彈窗應說明資料退場與刪除政策

    Example: 同意條款後可正常使用 AI 出題
      Given 使用者 "bob@example.com" 從未使用過 AI 出題功能
      When 使用者同意 AI 出題條款
      Then 系統應記錄同意時間
      And 使用者可正常使用 AI 出題功能

    Example: 不同意條款則無法使用 AI 出題
      Given 使用者 "bob@example.com" 從未使用過 AI 出題功能
      When 使用者拒絕 AI 出題條款
      Then AI 出題功能應不可用
      And 使用者仍可使用考古題練習功能

  # ==========================================================================
  # 十二、退場排程與監控
  # ==========================================================================

  Rule: 後置（事件）- 退場排程每日自動執行

    Example: 每日退場掃描正常執行
      When 系統於凌晨 03:00 執行每日退場掃描
      Then 掃描應記錄以下統計：
        | 指標               | 說明           |
        | 軟刪除題數         | 本次新增軟刪除 |
        | 硬刪除題數         | 本次永久刪除   |
        | 保護跳過題數       | 因保護條件跳過 |
      And 掃描日誌應保留供審計

    Example: 單次退場超過 1000 題時觸發告警
      Given 本次退場掃描偵測到 1,500 題符合退場條件
      When 系統準備執行批次軟刪除
      Then 系統應暫停退場並觸發告警通知管理員
      And 告警內容應包含「異常大量退場：1,500 題」
