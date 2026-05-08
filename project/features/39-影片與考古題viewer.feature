# language: zh-TW
@feature_39 @video_viewer @quiz_viewer @sprint_2_5
Feature: 影片 viewer 與考古題 viewer（端對端 UX）
  作為學習者，我想要不同檔案類型有專屬閱讀體驗：
  - 影片：時間戳側欄，點擊跳轉到對應段落
  - 考古題：一題一卡作答，答完才揭曉解析（避免洩答）

  # 對應：
  #   docs/sprint-2-cto-plan.md 順延項
  #   ux-redesign-plan.md Sprint 2 影片 viewer + 考古題 viewer

  Background:
    Given 已存在 PRO 用戶 "alice@example.com"

  @fullstack
  Rule: 影片 viewer 端對端
    Scenario: 上傳 MP4 → 開啟 watch 頁
      Given 用戶 "alice@example.com" 已上傳 "lecture.mp4" 解析狀態為 "success"
      And 該影片含 takeaway 鷹架且 chapter_heading="00:32-02:15 AI 三層級分類"
      When 用戶開啟 "/library/view/watch?docId={rid}"
      Then 應顯示 HTML5 video 播放器
      And 右側出現「時間戳重點」清單
      And 清單含一筆「00:32 AI 三層級分類」可點擊
      When 用戶點擊該時間戳項目
      Then 影片 currentTime 設為 32（會自動播放）

    Scenario: YouTube URL → embed iframe
      Given 用戶 "alice@example.com" 已提交 youtube_url
      When 用戶開啟 "/library/view/watch?docId={rid}&t=754"
      Then 應顯示 YouTube iframe（src 含 ?start=754）
      And 不顯示 HTML5 video 元素

    Scenario: 影片無時間戳鷹架 → 合理空態
      Given 用戶 "alice@example.com" 已上傳影片但無 chapter_heading 含時間戳
      Then 右側「時間戳重點」應顯示空態提示（K-06-video v1+ 才產出）
      And 不渲染清單項目

  @fullstack
  Rule: 考古題 viewer 端對端
    Scenario: 開啟考古題試題卷 → 一題一卡作答
      Given 用戶 "alice@example.com" 已上傳 "考古題.pdf" detected_content_type=practice_questions
      And 該資源解析時走 K-06-quiz prompt
      And 含 3 題已 approved questions + 對應 concept_extract scaffolds
      When 用戶開啟 "/library/quiz/quiz?docId={rid}"
      Then 應顯示 3 個題目卡片
      And 每題含 4 選項按鈕
      And 預設未顯示正確答案 / explanation / concept_extract
      When 用戶點擊第一題正確選項
      Then 應顯示「✓ 答對了！」+ explanation + 📌 考點解析（concept_extract）
      And 該題若有 pitfall scaffold 應顯示 PitfallAlert

    Scenario: 答錯題 → 揭曉正解 + concept_extract
      Given 同上場景但用戶選錯選項
      Then 應顯示「✗ 正確答案：(A)」（紅色）
      And 同時顯示 concept_extract 卡片
      And 該題鎖定不可重答

    Scenario: 解析 scaffolds 未含 questions → 合理空態
      Given 用戶 "alice@example.com" 已上傳 PDF 但 K-06-quiz 未產出題目
      When 用戶開啟 quiz 頁
      Then 顯示「此資源尚無解析出的題目」（合理空 per QA Layer 3）
      And 不顯示作答卡片
