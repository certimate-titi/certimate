@feature_40 @file_type_routing @sprint_3_p2
Feature: 多檔案類型 UX 分流（PPT / DOCX / 學習首頁 / 資源卡片）
  作為學習者，我想要根據資源類型看到專屬的視覺與 viewer：
  - PDF 學習指引：章節閱讀頁
  - PPT 簡報：投影片網格 / 全屏
  - 影片：時間戳跳轉播放
  - 考古題：一題一卡作答
  - 個人筆記：保留結構不蓋過
  - 學習首頁：今日 3 件事

  # 對應：
  #   docs/sprint-2-cto-plan.md / scaffold-redesign-plan.md P2
  #   ux-redesign-plan.md Sprint 3
  # 教育原理：File-Type Aware UI（不同媒材有不同學習負荷曲線）

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @fullstack
  Rule: PPT viewer 端對端
    Scenario: 上傳 PPTX → 解析後走 K-06-slides prompt
      Given 用戶 "alice@example.com" 上傳 "ai-fundamentals.pptx"
      Then 後端 _select_prompt_template 回傳 "resource_parser_slides"
      When 解析完成，用戶開啟 "/library/slides/slides?docId={rid}"
      Then 應顯示投影片網格（4 列）
      And 點擊任一張 → 進入全屏 viewer
      And 全屏頁含上下翻頁按鈕

    Scenario: PPT 不寫 takeaway（避免 fluency illusion）
      Given 同上 PPT 解析完成
      When 用戶查 /parsed scaffolds
      Then 所有 type=takeaway 的 retrieval_prompt 為「請補完論述」格式
      And 沒有「直接照抄 bullet」型的 takeaway content

  @fullstack
  Rule: DOCX 個人筆記
    Scenario: 上傳 DOCX → 走 K-06-notes prompt
      Given 用戶 "alice@example.com" 上傳 "我的筆記.docx"
      Then 後端 _select_prompt_template 回傳 "resource_parser_notes"
      When 解析完成
      Then scaffolds 不含 type=takeaway（避免蓋過原作者）
      And 含 type=elaborative challenge 質疑式內容
      And 可能含 type=pitfall 揪錯

  @fullstack
  Rule: 今日學習首頁 /today
    Scenario: 登入後可訪問 /today
      Given 用戶 "alice@example.com" 已登入
      When 用戶開啟 "/today"
      Then 應顯示「今日 3 件事」標題
      And 應有「⓵ 繼續讀」「⓶ 複習錯題」「⓷ Sprint 模擬測驗」3 卡
      And 含距考天數（若有）+ 連勝
      And 底部含「📊 完整儀表板」「🗺️ 知識圖譜」連結

    Scenario: 用戶尚未上傳資源 → 繼續讀卡片顯示空態 CTA
      Given 用戶 "alice@example.com" 帳號內無任何資源
      When 用戶開啟 "/today"
      Then 「⓵ 繼續讀」卡片顯示「尚未開始閱讀任何資源」
      And 含「去學習庫上傳資源 →」連結

  @fullstack
  Rule: ResourceCard 視覺差異化
    Scenario Outline: 不同類型顯示對應 icon / badge
      Given 用戶 "alice@example.com" 擁有 1 份 type="<type>" 資源
      When 渲染 ResourceCard
      Then 應顯示 icon "<icon>" 與 badge "<badge>"
      And 主 CTA 按鈕文字為 "<cta>"

      Examples:
        | type   | icon       | badge   | cta  |
        | pdf    | FileText   | PDF     | 讀   |
        | video  | Film       | 影片    | 看   |
        | slides | LayoutGrid | 簡報    | 過   |
        | audio  | Headphones | 音訊    | 聽   |
        | quiz   | HelpCircle | 試題卷  | 作答 |
