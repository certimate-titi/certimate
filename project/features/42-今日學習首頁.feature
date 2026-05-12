# language: zh-TW
@frontend @fullstack
Feature: 42 今日學習首頁

  作為一個備考用戶
  我希望登入後看到「今日 3 件事」學習首頁
  讓我快速知道現在該做什麼，而非面對一堆數字報表

  Background:
    Given 使用者已登入

  # ── Greeting 與 Meta ──────────────────────────────

  Rule: 今日學習首頁應根據時段顯示問候語與備考 Meta

    Example: 顯示問候語與使用者名稱
      When 使用者開啟 /today 頁面
      Then 頁面應顯示時段問候語（早安/午安/晚安/夜深了）
      And 問候語後方應帶有使用者 displayName

    Example: 顯示距考天數與連續天數
      Given 使用者距下次考試 14 天且已連續學習 7 天
      When 使用者開啟 /today 頁面
      Then 頁面應顯示「距下次考試 14 天」
      And 頁面應顯示「連續 7 天」streak badge

    Example: 無考試日期時不顯示倒數
      Given 使用者未設定考試日期
      When 使用者開啟 /today 頁面
      Then 頁面不應顯示距考天數區塊

  # ── 三件事卡片（有資料） ──────────────────────────

  Rule: 今日 3 件事應根據後端資料渲染對應卡片

    Example: 繼續讀卡片（有上次中斷資源）
      Given 使用者上次閱讀的資源為「民法概要第三章」
      When 使用者開啟 /today 頁面
      Then 應顯示「繼續讀」卡片，標題含「民法概要第三章」
      And 卡片應連結至對應的閱讀頁面

    Example: 複習錯題卡片（有待複習題目）
      Given 使用者有 5 題待複習
      When 使用者開啟 /today 頁面
      Then 應顯示「複習錯題」卡片，標題含「5 題待複習」
      And 卡片應連結至 /knowledge/wrong-answers

    Example: Sprint 模擬測驗卡片
      When 使用者開啟 /today 頁面
      Then 應顯示「Sprint 模擬測驗」卡片
      And 卡片應連結至 /exam/setup

    Example: 距考 14 天以內顯示緊急建議
      Given 使用者距下次考試 10 天
      When 使用者開啟 /today 頁面
      Then Sprint 模擬測驗卡片應顯示「距考試 10 天，建議安排今日測驗」

  # ── 鷹架到期提示 ──────────────────────────────────

  Rule: 當有 SM-2 鷹架到期時應顯示提示

    Example: 顯示鷹架到期數量
      Given 使用者有 3 個鷹架到期
      When 使用者開啟 /today 頁面
      Then 頁面應在複習區塊顯示「3 個學習鷹架到期」提示

    Example: 無鷹架到期時不顯示
      Given 使用者有 0 個鷹架到期
      When 使用者開啟 /today 頁面
      Then 頁面不應顯示鷹架到期提示

  # ── 空態渲染 ──────────────────────────────────────

  Rule: 空態應提供引導文字與操作入口

    Example: 繼續讀空態
      Given 使用者未閱讀過任何資源
      When 使用者開啟 /today 頁面
      Then 繼續讀區塊應顯示「尚未開始閱讀任何資源」
      And 應提供「去學習庫上傳資源」連結

    Example: 複習錯題空態
      Given 使用者無待複習題目
      When 使用者開啟 /today 頁面
      Then 複習區塊應顯示「目前沒有待複習的題目」

  # ── Layer 3 空態：查 Job 表 ──────────────────────

  Rule: 空態時應主動查詢 resource_parse_jobs 確認是否為解析失敗

    Example: 繼續讀空態偵測到資源解析失敗
      Given 使用者有 1 份資源狀態為 FAILED，failure_reason 為「PDF 格式不支援」
      And 使用者未閱讀過任何資源
      When 使用者開啟 /today 頁面
      Then 繼續讀區塊應顯示紅色警示卡
      And 警示卡應包含失敗資源名稱與 failure_reason

    Example: 複習空態偵測到資源解析失敗
      Given 使用者有 2 份資源狀態為 FAILED
      And 使用者無待複習題目
      When 使用者開啟 /today 頁面
      Then 複習區塊應顯示紅色警示卡
      And 警示卡應包含失敗數量與 failure_reason

    Example: 空態無解析失敗時不顯示警示
      Given 使用者無 FAILED 狀態的資源
      And 使用者未閱讀過任何資源
      When 使用者開啟 /today 頁面
      Then 繼續讀區塊不應顯示紅色警示卡

  # ── 快速連結 ──────────────────────────────────────

  Rule: 頁面底部應提供其他工具的快速連結

    Example: 顯示快速連結
      When 使用者開啟 /today 頁面
      Then 應顯示「完整儀表板」、「知識圖譜」、「自由練習」、「帳號設定」四個快速連結
