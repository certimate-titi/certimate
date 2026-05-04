# 代辦項目及處理程序紀錄

> **🔒 SSOT 宣告**：本檔（`docs/ToDoList.md`）為待辦清單**唯一真實來源**。專案根目錄 `ToDoList.md` 為 symlink 指向此檔。所有巡檢腳本 / agent 寫入必須以此路徑為準。歷史 session 筆記已歸檔至 `docs/archive/`。（建立於 2026-05-03）

## 待辦事項
**最後更新**：2026-05-04 TiTi Commander 排程巡檢 — 修復：🔴1 完成（`/edu-console` DPA UI 已實作）；剩餘未解決：🔴4 🟠5 🟡3 共 12 項（其中 3 項待後端先補 API）

**權限模型備忘**（2026-05-03 最終確認）：

| 帳號類型 | 內容 |
|---------|------|
| 管理者 `ADMIN` | 後台基本權限（用戶問題協助排除、客服級操作）+ 自動含所有 user-facing tier 功能（含 ULTRA） |
| 管理者 `SUPER_ADMIN` | 含所有 ADMIN 權限 + **高等設定權限**：Prompt 模板設定、金額/預算上限、Feature Flag、系統設定、AI 模型路由、成本監控等 |
| 用戶 tier `FREE` | 限制版（10 題/次、3 次免費 AI chat、詳解 select-none） |
| 用戶 tier `PRO_199` | 50 題/次 + 無限制文件 / YouTube 解析 + 基礎 AI（不含 PRO_PLUS-only chat） |
| 用戶 tier `PRO_PLUS_399` | 100 題/次 + Vision OCR + 對話式 AI 教練 + 動態弱點出題 |
| 用戶 tier `ULTRA_1599` | 無題數上限 + 完整 AI 教練 + 教育管理（建立 EDU 學生帳號最多 30 名）+ 進階出題配方 |
| **附屬 `EDU`**（學生帳號）| **附屬於 ULTRA 機構底下**；50 題/次、共用機構配額池、基礎 AI chat、無限文件解析、無 Vision OCR；不可自行訂閱（僅機構管理員透過 CSV 匯入或邀請建立）；被指派時若已有個人付費訂閱會自動暫停計費 |

**守衛規則**：
- `(isUltra \|\| isAdmin)` — 守 user-facing tier 功能（兩種管理者皆 bypass）
- `isAdmin` — 守一般管理者後台（ADMIN + SUPER_ADMIN 皆可進）
- `isSuperAdmin` — 守高等設定（Prompt / 預算 / 系統設定 / Feature Flag 等）— 純 ADMIN 不可

**待補稽核**（次要）：`/super-admin/settings/*`、`/super-admin/prompt-templates/`、`/super-admin/cost-monitor/`、`/super-admin/settings/flags`、`/super-admin/settings/plans` 等高等設定頁應改用 `isSuperAdmin` 守衛（目前皆用 `isAdmin`）。後端 `require_super_admin` 已存在，需 audit endpoint 一致性。

## 🔴 Feature 缺失 — 需補 Gherkin Scenario

- [x] `/dashboard` — ~~科目切換器 (SubjectSwitcher) 缺 Feature Scenario（Feature 13 全 35 個 @ignore 需解封或重寫）~~ Feature 13 已有 36 個 active Example（0 @ignore），含科目切換器 Rule (L40)（確認：2026-04-27 自動巡檢）
- [x] `/dashboard` — ~~複習日曆 + 月份切換缺 Feature Scenario（Feature 13 全 @ignore）~~ Feature 13 Rule「艾賓浩斯複習月曆」(L250) 含月份參數驗證（確認：2026-04-27 自動巡檢）
- [x] `/dashboard` — ~~每日任務 (DailyQuestCard) 缺 Feature Scenario（Feature 13 全 @ignore）~~ Feature 13 Rule「每日首次登入應自動產生 1-3 個微任務」(L96) + 任務完成觸發 (L108)（確認：2026-04-27 自動巡檢）
- [x] `/dashboard` — ~~備考模式標籤 Sprint/Standard/Mastery 無任何 Feature 覆蓋~~ Feature 13 Rule (L379-411) 含 Sprint/Standard/Mastery 三個 Example Scenario，前端 page.tsx 亦已實作三模式 UI（確認：2026-04-30 自動巡檢）
- [x] `/dashboard` — ~~核心指標卡（streak、答題數、答對率、預測及格率）缺 Feature Scenario~~ Feature 13 Rule「每日登入並學習應累積連勝天數」(L73) 含 streak_7 驗證（確認：2026-04-27 自動巡檢）
- [x] `/knowledge` — ~~科目切換器無 active Scenario（Feature 03 全 @ignore）~~ Feature 03 有 8 個 active scenario（科目切換、佈局、AI 教練互動、節點顏色），9 個仍 @ignore（確認：2026-04-26 自動巡檢）
- [x] `/knowledge/mindmap` — ~~ForceGraph/MindMapTree 視圖切換無任何 Feature 覆蓋~~ Feature 03b Rule「知識地圖中央區應提供 ForceGraph / MindMapTree / Document 三視圖切換」(L231) 含 3 個 Example（預設 ForceGraph、切換 MindMapTree、切換 Document）（確認：2026-04-29 自動巡檢）
- [x] `/exam/results` — ~~成績卡片下載按鈕無 Feature Scenario~~ Feature 06 Rule (L143-148)「下載成績卡片按鈕應顯示為 placeholder 未實作狀態」含 Example Scenario（確認：2026-04-30 自動巡檢）
- [x] `/exam/workspace` — ~~番茄鐘計時器 Feature 21 存在但 0 active Scenario~~ Feature 21 已有 15 個 active Scenario，無 @ignore 標記（確認：2026-04-25 自動巡檢）
- [x] `/account/my-subjects` — ~~刪除科目功能無任何 Feature 覆蓋~~ Feature 13 Rule「帳戶頁面科目編輯與移除」(L357) + 前端 handleDelete 已實作（確認：2026-04-27 自動巡檢）
- [x] `/account/resource-library` — ~~資源分享功能無 active Feature Scenario（Feature 11 @wip）~~ Feature 11 已有 15 個 active Scenario，無 @wip 標記（確認：2026-04-25 自動巡檢）
- [x] `/library` — ~~Tab 切換無任何 Feature 覆蓋~~ **頁面不存在**（`frontend/app/library/page.tsx` 不存在），此條目為過時參照，應移除（確認：2026-04-29 自動巡檢）
- [x] `/edu-console` — ~~CSV 匯入 / 新增學員 Feature 10 全 @ignore，無 active Scenario~~ Feature 10 已有 55 個 active Example（@command 標記非 @ignore），含 CSV 匯入、DPA 簽署、學員上限等 Scenario（確認：2026-04-27 自動巡檢）
- [x] `/super-admin/settings/flags` — ~~Feature Flag 設定無任何 Feature 覆蓋~~ Feature 12c 含「更新 Feature Flag 上線比例」+「Feature Flag 切換開關」Rule（確認：2026-04-27 自動巡檢）
- [x] `/super-admin/settings/plans` — ~~方案配額管理無 active Feature Scenario~~ Feature 12c Rule「方案配額表格應支援行內編輯與儲存」已 active（確認：2026-04-27 自動巡檢）
- [x] `/super-admin/users/[userId]` — ~~用戶詳情頁無 active Feature Scenario~~ Feature 12 Rule「用戶詳情頁應回傳六個資訊區塊」已 active（確認：2026-04-27 自動巡檢）
- [x] `/review` — ~~Feature 07（錯題複習與 AI 教練）整個 Feature 全 @ignore~~ Feature-level @ignore 已移除（改為 @query），6 個 scenario-level @ignore 已解封（側邊列表切換→@playwright-e2e、答案對比→@playwright-e2e、引用來源切換、毛玻璃遮罩、月配額限制、空狀態）。後端 step definitions 齊全。13 個 AI 安全 scenario 維持 @skip（標記 @infra-heavy，待基礎設施就緒）（修復：2026-04-25 自動巡檢，**高優先已解決**）
- [x] `/practice` — blindInferenceService（信心度校準）Feature 20 核心後端 Scenario 已全部 active，僅 2 個 UI scenario 仍 @ignore（確認：2026-04-24 15:08 自動巡檢）
- [x] `/super-admin/settings/version` — ~~版本資訊頁無任何 Feature 覆蓋~~ Feature 12c Rule「版本資訊頁應顯示後端 / 前端 build 資訊」(L260) 含 Example（顯示 commit、deployed_at、revision + 複製按鈕）（確認：2026-04-29 自動巡檢）
- [x] `19-交錯練習.feature` + `32-節點練習模式.feature` — ~~Feature 檔案存在但 Scenario 數量為 0~~ **已有完整 Scenario**（19：8 Examples, 32：9 Examples）（確認：2026-04-24 自動巡檢；46-Canvas.feature + 46b-Analytics.feature 已於 2026-04-28 整檔刪除，CEO 簽核移除 PRD-046 Canvas 功能）
- [x] `/dashboard` — ~~待辦提醒（activityItems）缺 Feature Scenario（Feature 13 全 @ignore）~~ Feature 13 Rule「儀表板應包含考試倒數、雷達圖、快速上傳區與待辦提醒」(L59) 已 active（確認：2026-04-27 自動巡檢）
- [x] `/dashboard` — ~~DomainRadarChart（領域雷達圖）缺 Feature Scenario（Feature 13 全 @ignore）~~ Feature 13 Rule「雷達圖應顯示各領域的強度資料」(L228) 含能力分布驗證（確認：2026-04-27 自動巡檢）
- [ ] `/dashboard` — StudyBuddyBanner（ULTRA 共讀橫幅）無任何 Feature 覆蓋（首見：2026-04-27）
- [x] `/super-admin/audit-logs` — ~~審計日誌無 active Feature Scenario（Feature 12 全 @ignore）~~ Feature 12 已有 35 個 active Example（0 @ignore），含 10 處審計日誌記錄驗證（確認：2026-04-27 自動巡檢）
- [x] `/super-admin/retirement` — ~~Feature 25（AI 考題退場與放榜確認）全 @ignore，無 active Scenario~~ Feature 25 已有 36 個 active Example（0 @ignore），涵蓋來源標記、品質管理、退場流程（確認：2026-04-27 自動巡檢）
- [x] `/super-admin/default-resources` — ~~預設資源 Fork 管理無 active Feature Scenario（Feature 34 無對應前端頁面 Scenario）~~ Feature 34 已有 9 個 active 場景，含 fork、冪等性、atomicity、rollback 等（確認：2026-04-27 自動巡檢）
- [x] `/super-admin/platform-subjects` — ~~平台科目管理無任何 Feature 覆蓋~~ Feature 12c Rule「平台科目管理頁應支援列表/編輯/啟停用」(L271-282) 含 Scenario，Feature 34 亦覆蓋相關 API（確認：2026-04-30 自動巡檢）
- [x] `/resources/[id]/candidates` — ~~前端頁面尚未建立~~ `frontend/app/resources/[id]/candidates/page.tsx` 已建立，Feature 23 Rule (L132) Scenario 覆蓋完整（確認：2026-04-30 自動巡檢）
- [x] `/exam/workspace` — ~~Feature 05 Certi 打氣語句缺實作~~ 嚴格 TDD 完成：後端新增 `GET /api/v1/exams/{id}/intro` 包裝既有 `EncouragementService.generate('pre_exam_cheer', learning_state)`，回應含 coach_name='Certi'、message、learning_state（streak_days + exams_taken_recent）；前端 examService.getIntroEncouragement + workspace useEffect 載入後 5 秒自動隱藏的 banner（data-testid="certi-intro-banner"）；F05 既有 step bug 修正（create_token → generate_token）+ Then 斷言加嚴；F05 BDD 全綠 14 scenarios / 130 steps（修復：2026-05-04）
- [x] `/edu-console` — ~~Feature 10 L58-65 規定「機構管理員首次匯入學生前須簽署資料處理合約（DPA）」；`edu-console/page.tsx` 無 DPA 相關 UI~~ edu-console/page.tsx 新增 DPA 簽署 modal（DpaSignModal）+ 底部未簽署 Banner + handleImportClick 攔截邏輯；呼叫 `adminService.getDpa()` 查狀態、`adminService.signDpa(signerName)` 簽署；簽署後自動開啟 CSV 匯入 modal（修復：2026-05-04 TiTi Commander 排程巡檢）
- [x] `/practice` — ~~Feature 28（階層式難度遞進）回溯邏輯前端未整合~~ Schema Analysis 確認後端 difficultyProgressionService 完整 + frontend service client 已存在但未呼叫；practice/page.tsx 整合：答錯時呼叫 `nextStrategy(subjectId, {current_node_id, original_node_id, consecutive_wrong})`；若 `next_action === 'backtrack'` 顯示 banner（data-testid="backtrack-banner"）+「切換至父節點」按鈕；切換後 reload 該父節點題目；F28 BDD 13 scenarios / 98 steps 全綠（修復：2026-05-04）
- [x] `/exam/setup` — ~~Feature 19（交錯練習）規定測驗設定頁可切換題目排列模式（interleaved / grouped / sequential），但頁面目前無此 UI 選項~~ `orderMode` state 及三按鈕 UI（🔀交錯/📦分組/📈依難度）已確認存在於 page.tsx，先前誤報（確認：2026-04-29 自動巡檢）
- [x] `/pricing` — ~~PRO_PLUS_399 方案功能矩陣「進階 AI 教練」顯示 false~~ Feature 07 明確規定「進階 AI 教練為 ULTRA 方案專屬功能」（L151-153），PRO_PLUS_399 僅享基礎 AI 教練（100 次/月、max_tokens 2048）；定價頁顯示正確，先前誤報源於 Feature 03 與 Feature 07 混淆（確認：2026-05-01 TiTi Commander 巡檢）
- [x] `/knowledge/mindmap` — ~~節點點擊互動僅 setSelectedNodeId 無任何視覺反饋~~ Schema Analysis 確認 `knowledgeService.getNodeDetail` 已存在；mindmap/page.tsx 整合：點擊節點後呼叫 getNodeDetail 載入詳情並顯示**側邊面板**（data-testid="mindmap-node-detail-panel"，固定右側 384px 寬）：節點名、來源資訊、citationText 摘要（最多 400 字）、「開始練習此節點」按鈕（連 /practice?nodeId=...）、「在學習庫查看詳情」按鈕（連 /knowledge?subjectId=...&nodeId=...）+ 關閉按鈕（X）；F03b BDD 9 scenarios 沒回歸（修復：2026-05-04）
- [x] `/exam/results` — ~~Feature 06 規格「LinkedIn 分享 / 下載成績卡片為 placeholder 即將推出」與現行實作不符~~ Feature 06 L136-148 已更新：分享按鈕應開啟 LinkedIn 分享視窗、下載按鈕應觸發 PNG 下載（檔名 `CertiMate_Score_{score}_{YYYY-MM-DD}.png`）；spec 與實作對齊（修復：2026-05-03 TiTi Commander）

---

## 🟠 實作缺失 — 需補前端功能

- [x] `/exam/results` — ~~Feature 06 描述「逐題解析」查看，但頁面無跳轉逐題解析的按鈕或入口~~ 頁面 L240 已有 Link 至 `/review?examId=${examId}&all=1`，文字「逐題解析（含答對題）」，入口完整（確認：2026-04-29 自動巡檢）
- [x] `/exam/results` — ~~成績卡片下載按鈕功能為 alert stub（`"即將推出"`），需實作實際下載功能~~ 已改由 html2canvas@1.4.1 實作（非 alert stub），html2canvas 已在 package.json 確認安裝；仍無 Feature Scenario 覆蓋（確認：2026-04-30 自動巡檢）
- [x] `/exam/workspace` — ~~Feature 21（番茄鐘）存在，但頁面無 pomodoro/番茄鐘相關實作邏輯，需確認並實作~~ PomodoroTimer 已在 line 226 確認渲染（`<PomodoroTimer examDurationSec={totalTimeLimit} paused={isPaused} />`），Feature 21 覆蓋完整（確認：2026-04-29 自動巡檢）
- [x] ~~`/knowledge` — Feature 46（知識地圖 Canvas 三層 Zoom）存在，頁面使用 ForceGraph 但三層 Zoom 邏輯未明確實作，需對照 PRD-046（首見：2026-04-24）~~ **CEO 2026-04-24 決議移除 PRD-046 Canvas（合併至既有 ForceGraph mindmap）**；spec 46 + 46b 與 frontend/lib/analytics.ts 已於 2026-04-28 整檔刪除
- [x] `/practice` — no-questions 空態已新增「前往出題」快捷按鈕（自動帶入當前 nodeId），引導至 `/exam/setup`（修復：2026-04-24 自動巡檢）
- [x] `/super-admin/anomaly` — ~~Feature 16「批次修復」情境缺乏對應 UI 元素~~ Spec 已存在（Feature 16 L130-149）；anomaly/page.tsx 新增多選 checkbox 欄位（thead 全選、tbody per-row）+ 「批次修復」按鈕（依序 PATCH /admin/anomalies/{id} status:resolved，部分失敗時保留勾選 + 紅 XCircle icon）；本地端對端驗證：3 筆 fixture seed → 全選 → 批次修復 → 全部標 resolved + 訊息「✓ 已修復 3 筆異常」（修復：2026-05-03）
- [x] `/review` — ~~KaTeX 渲染待確認~~ MathContent component 確認使用 `rehype-katex` + `remark-math` + `katex/dist/katex.min.css`，透過 ReactMarkdown 實作完整 KaTeX 數學公式渲染；Feature 07 仍無對應 Scenario 但功能實作完整（確認：2026-04-30 自動巡檢）
- [x] `/knowledge` — ~~「+ 新增資源」按鈕點擊後導向 `/dashboard` 而非直接開啟上傳 modal~~ knowledge/page.tsx L475 已確認 `Link href="/dashboard"`，跨頁導航行為符合現行設計；待補 Feature 03 Scenario 但功能正常（確認：2026-05-03 內容驗證）
- [x] `/exam/workspace` — ~~Feature 20 信心度校準規格「信心度標記以三個小圖示（😰😐😎）呈現在答案選項下方」~~ workspace/page.tsx 答案選項下方新增 confidence-selector（per question），confidences state 為 Record<questionId, confidence>；examService.submit 擴充 confidence 欄位，POST /answers 多帶 confidence；後端 SaveAnswerRequest 既有 confidence 欄位（exam.py:122）（修復：2026-05-03）
- [x] `/practice` — ~~Feature 20 信心度校準規格「信心度標記以三個小圖示（😰😐😎）呈現在答案選項下方」~~ practice/page.tsx 答題區新增 `confidence-selector`（😰完全猜測 / 😐有點把握 / 😎非常確定）；`practiceService.submitAnswer` 擴充支援 `userConfidence`，後端 `PracticeSubmitRequest` 接受 `user_confidence` 欄位，預設值 somewhat（修復：2026-05-03 TiTi Commander）
- [x] `/exam/setup` — ~~Feature 04 規定「ULTRA 方案可自訂 Bloom 認知層級比例」，但進階出題配方面板由 `isAdmin` 守衛而非 `isUltra`；ULTRA 付費用戶無法存取此功能~~ setup/page.tsx 守衛改為 `(isUltra || isSuperAdmin)`；同步修復 auth-context：保留 SUPER_ADMIN 區分（不再攤平成 ADMIN），新增 `isSuperAdmin` flag；ULTRA tier + SUPER_ADMIN 可看面板，純 ADMIN 不可（對齊 Feature 04 規格）（修復：2026-05-03 TiTi Commander）
- [ ] `/exam/setup` — Feature 04 規格描述測驗生成應使用 SSE 推送即時進度；前端目前使用 `ExamLoadingOverlay` 模擬假階段動畫，未實際訂閱 SSE 端點（首見：2026-05-01）
- [ ] `/account` — 通知偏好（daily_reminder / pre_exam_reminder / weekly_report）需改為後端 API 儲存（目前僅存 localStorage）；Feature 22 規格描述為 API 操作，規格與實作不同步（首見：2026-05-01）
- [ ] `/knowledge` — Feature 27（個人化錯題地圖）要求「以紅/橘/綠色視覺化呈現個人弱點分佈的獨立熱力圖層」；knowledge/page.tsx 目前僅以 `mastery_color` 近似（由 ForceGraph node color 呈現），缺乏 Feature 27 規格描述的「熱力圖可展開查看節點下錯題明細」互動行為（首見：2026-05-04）
- [x] `/exam/setup` — ~~**P1 BUG**: `TIER_QUESTION_LIMITS` PRO_PLUS_399 的 `max` 設為 50，Feature 04 L71-83 明確規定 PRO_PLUS 上限為 100 題~~ 已修正：`max: 50` → `max: 100`，`upgradeMessage` 更新為「PRO_PLUS 方案每次測驗最多 100 題，升級 ULTRA 無題數上限」（修復：2026-05-03 TiTi Commander 排程巡檢）
- [x] `/exam/setup` — ~~**P2 BUG**: PRO_199 升級提示文字「升級 ULTRA 最多可出 100 題以上」錯誤~~ 已修正：PRO_199 → 「升級 PRO_PLUS 最多可出 100 題」（對齊 Feature 04 L65）；PRO_PLUS_399 → 獨立文字「升級 ULTRA 無題數上限」（修復：2026-05-03 TiTi Commander 排程巡檢）
- [x] `/exam/results` — ~~Feature 19 L85-89 規格要求結果頁顯示排列模式標籤「交錯練習」及提示文字~~ 已修正：新增 `questionOrderMode` 至 Exam 型別（`types/models.ts`）、`services.ts` 映射 `question_order_mode`、結果頁顯示🔀交錯練習標籤 + 提示文字「交錯練習有助於長期記憶，持續使用效果更佳」（修復：2026-05-03 TiTi Commander 排程巡檢）
- [x] `/practice` — ~~Feature 32 要求空節點空態有「選擇其他節點」與「回知識圖譜」兩個操作按鈕~~ 兩個按鈕皆已實作於 `page.tsx` line 384（選擇其他節點）和 line 388-393（回知識圖譜，連結至 `/knowledge`）（確認：2026-04-26 自動巡檢）
- [x] `/account/resource-library` — FAILED 資源 failure_reason 已透過 title tooltip 向用戶呈現（hover「解析失敗」可見詳細原因），並透過 resourceParseService.getStatus() 主動輪詢（確認：2026-04-25 自動巡檢）

---

## 🟡 空態補強 — 需查 Job 表

- [x] `/knowledge` — documents.length === 0 空態已區分「從未上傳」；FAILED 文件自動查詢 `resource_parse_jobs.failure_reason` 並顯示（修復：2026-04-24 自動巡檢）
- [x] `/knowledge/mindmap` — mindMapNodes.length === 0 空態已根據文件狀態區分四種情境：無資源/全部失敗/處理中/未萃取（修復：2026-04-24 自動巡檢）
- [x] `/practice` — phase === 'no-questions' 空態已新增提示訊息（AI 出題可能失敗）及「前往出題」快捷按鈕（修復：2026-04-24 自動巡檢）
- [x] `/exam/setup` — documents.length === 0 空態已新增提示：若已上傳資源但為空，引導至知識庫查看解析狀態（修復：2026-04-24 自動巡檢）
- [x] `/library` — ~~頁面空態情況不明~~ **頁面不存在**（`frontend/app/library/page.tsx` 不存在），此條目為過時參照，應移除（確認：2026-04-29 自動巡檢）
- [x] `/practice` — ~~no-questions 空態有文字 hint 提示，但**未實際查詢 resource_parse_jobs 取得 failure_reason**~~ practice/page.tsx 已實作 Layer 3：phase 進入 no-questions 時 useEffect 查 documentService.list() 過濾 activeSubjectId + status==='FAILED'，逐個呼叫 resourceParseService.getStatus() 取得 failure_reason，UI 顯示紅色警告塊列出最多 3 個（修復：2026-05-03）
- [x] `/review` — ~~wrongQuestions.length === 0 時未查詢後端 job 表~~ 嚴格 TDD 五階段完成（Schema Analysis → Step Template → Red 404 → Green → Refactor）：後端新增 `GET /api/v1/exams/recent-failures` endpoint 查當前用戶最近 5 筆 status=FAILED 測驗；前端 examService.getRecentFailures + /review 空態 useEffect 觸發；UI 條件渲染：有 FAILED → 紅色警告塊「無錯題記錄」+ 失敗列表；無 → 原「全部答對！」；F07 BDD 新增 Rule + 2 Examples 全綠（修復：2026-05-04）
- [x] `/account/resource-library` — FAILED 資源 badge 已顯示，failure_reason 透過 tooltip 呈現（確認：2026-04-25 自動巡檢）
- [x] `/super-admin/exam-import` — Import job FAILED 狀態已顯示 errorMessage（inline 顯示於 ImportJobsList 元件），無 failure_reason 但使用 error_message 欄位，功能正常（確認：2026-04-25 自動巡檢）
- [x] `/schedule` — ~~recs.length === 0 時 Layer 3 違規~~ Schema Analysis（2026-05-04）：排程建議為**同步計算**（基於 user_subjects 即時生成），無對應 async job 表可查；空態的唯一合理解釋即「用戶尚無備考科目」（onboarding 未完成或主動移除全部）；F09 L22-27 已有對應 Rule「使用者必須至少有一個備考科目才能使用排程」；**不適用 Layer 3**，現行訊息正確
- [x] `/account/weekly-reports` — ~~reports.length === 0 時 Layer 3 違規~~ Schema Analysis（2026-05-04）：WeeklyReport model 無 status 欄位（成功生成才會建 row），cron 失敗不會留 FAILED row；查 job 失敗需另設監控基礎設施（MaintenanceTask 或 Cloud Logging）；**不適用前端 Layer 3**，cron 健康監控應由 cloud-engineer 在維運層處理（已記入「待部署」項目）
- [x] `/knowledge/mindmap` — ~~mindMapNodes.length === 0 空態顯示「上傳教材後系統會自動生成」，未查詢 resource_parse_jobs~~ mindmap/page.tsx 已實作 Layer 3：mindMapNodes 為空且 loading 結束時 useEffect 查 documentService.list() 過濾 activeSubjectId + FAILED，呼叫 getStatus() 取 failure_reason；空態 UI 改為條件渲染：有失敗時顯示紅色警告塊，無失敗才顯示原「上傳教材後生成」提示（修復：2026-05-03）
- [x] `/knowledge` — ~~documents 與 nodes 皆空時顯示靜態提示，未查詢 resource_parse_jobs~~ knowledge/page.tsx L243-251 已實作 Layer 3：useEffect 自動對 FAILED 文件呼叫 `resourceParseService.getStatus()` 並寫入 `parseJobFailures` state，UI 透過 tooltip 呈現 failure_reason（確認：2026-05-03 深度驗證）
- [x] `/verify-email/sent` — ~~resend 重寄失敗時 `catch {}` block 為空（silent fail），使用者無任何錯誤提示~~ 已修復：新增 `resendError` state，catch block 顯示「驗證信寄送失敗，請稍後再試。」紅色提示框，同時重設 cooldown 讓使用者可立即重試（修復：2026-04-29 自動巡檢）

---

### ✅ 用戶管理前端修復（P1） — 完成於 2026-04-17
- ✅ 新增「發送通知」按鈕至 `users/[userId]/client.tsx`（彈窗輸入 → Email 發送）
- ✅ 停權/恢復按鈕動態切換（active 顯示「停權」、suspended 顯示「恢復」）
- ✅ 停權/恢復後自動發送通知信（`send_suspension_email` / `send_restoration_email`）
- ✅ `notify_user` 後端實際發送 Email（`send_admin_notification_email`）
- ✅ 前端 `services.ts` 新增 `notifyUser()` API 函式

### ✅ Prompt 模板前端修復（P1） — 完成於 2026-04-17
- ✅ 編輯表單新增 model 下拉選單（gemini-2.5-flash / gemini-2.5-pro / claude-3.5-sonnet / claude-3.5-haiku / gpt-4o / gpt-4o-mini）
- ✅ 儲存時自動傳送 model 參數至後端 PATCH API
- ~~prompt無法編輯~~ → ✅ 已確認可編輯（system_prompt / user_prompt / temperature）

### ✅ SSO 密碼重設流程 — 已完成（驗證於 2026-04-17）
- ✅ Backend：`forgot_password()` 生成 reset token + 發送 Email
- ✅ Backend：`reset_password()` 驗證 token + 設定密碼
- ✅ Backend：`login()` SSO 用戶無密碼時回傳專用錯誤訊息
- ✅ Frontend：`/forgot-password` 頁面（含 SSO 提示）
- ✅ Frontend：`/reset-password` 頁面（密碼強度驗證）
- ✅ Email 模板：`send_password_reset_email`（含 SSO 提示）

---

### ✅ RAG 物理級跳轉完善（P2） — 完成於 2026-04-17
- ✅ ResourceChunk model 新增 `anchor_id`、`highlight_line_start/end`、`highlight_char_start/end` 欄位
- ✅ Alembic migration 056 建立
- ✅ DBML (erm.dbml) 同步更新
- ✅ `get_node_source()` API 增強 — 回傳 `highlight` 物件（anchor_id + line/char 範圍）

### ✅ 向量快取機制（P2） — 完成於 2026-04-17
- ✅ `EmbeddingService.embed_query()` 自動快取（LRU 1000 + TTL 24h）
- ✅ 支援 Redis（優先）+ 記憶體 fallback
- ✅ 新增 `get_cache_stats()` 供 admin 監控快取命中率
- ✅ 環境變數：`EMBEDDING_CACHE_MAX_SIZE`、`EMBEDDING_CACHE_TTL`

### ✅ 系統設定頁面重組（P3） — 完成於 2026-04-17
- ✅ 拆分為 6 個獨立子頁面（含 shared layout + sidebar 導航）：
  - `/super-admin/settings` — AI 模型路由
  - `/super-admin/settings/plans` — 方案限額
  - `/super-admin/settings/announcements` — 公告管理
  - `/super-admin/settings/flags` — Feature Flags
  - `/super-admin/settings/admins` — 管理員帳號
  - `/super-admin/settings/version` — 版本資訊

---

## 完成事項

### ✅ 13. GCP Billing Export 功能實現 — 完成於 2026-04-17

**成本監控中心（Feature 33）的 BigQuery Billing Export 模組實現**：
- ✅ `GcpBillingService` — SQL 查詢層（使用 `export_time` 欄位）
- ✅ 環境變數配置（`config.py`）
- ✅ 詳細錯誤處理與日誌
- ✅ BDD 測試集成（test hooks）
- ✅ 配置指南文檔（`GCP_BILLING_EXPORT_SETUP.md`）
- ✅ 實現總結文檔（`BILLING_EXPORT_COMPLETION.md`）
- [ ] **待部署**：Cloud Run 環境變數 + Service Account key 掛載
- [x] **雲端驗證**（2026-05-04 commit `432ac91` 部署後完成端對端）：seed 7 測試帳號 → cloud Cloud Run 驗證 13 條守衛
  - ADMIN/FREE：cost-monitor/settings/prompt-templates 三頁皆 redirect→dashboard ✅；/exam/setup 進階配方+教育管理 nav 顯示 ✅
  - USER/ULTRA：/super-admin/dashboard redirect→/dashboard ✅；進階配方+教育管理 nav 顯示 ✅；平台管理 nav 隱藏 ✅
  - USER/FREE：所有付費/admin 元素皆隱藏 ✅
  - SUPER_ADMIN：cost-monitor/settings/prompt-templates 三頁皆可進 ✅
  - console 0 errors
- [ ] **Frontend Playwright BDD 補測**（2026-05-03 完整補測時識別的債務）：以下純前端守衛與 UI 行為需實作 Playwright step definitions
  - L58 ULTRA Bloom 守衛（Feature 04 L185-211 spec 已存在，缺 frontend step：`使用者 "ultra@example.com" 提交測驗設定...自訂 Bloom 比例為...`）
  - isSuperAdmin 守衛 redirect 行為（純 ADMIN 進高等設定頁應 redirect 至 dashboard，缺 spec + step）
  - L95 `/practice` Layer 3 空態（FAILED 文件 → 紅色警告塊，缺 spec + step）
  - L101 `/knowledge/mindmap` Layer 3 空態（缺 spec + step）
  - L75 `/exam/workspace` 信心度 emoji UI 互動（Feature 20 backend 已有 spec，缺 frontend UI step）
  - 規模評估：5 個 features × 平均 1-2 小時 = 約 10 小時。建議拆批處理

**API 端點**：`GET /admin/cost/gcp/services` — 查詢當月 GCP 服務分類成本

*詳細處理紀錄：`docs/BILLING_EXPORT_COMPLETION.md`*

---

### ✅ 12. RAG 資料流程差異分析 + 平台管理功能審查 — 完成於 2026-04-17

**RAG 資料流程_修正版 vs 實作差異**（整體完成度 85-90%）：
- ✅ 結構化提煉（6 章心智圖）、動態增刪、權威優先、二階段檢索、Mastery 引擎、配額控制 — 完全實現
- ⚠️ 物理級跳轉（anchor_id 缺失）、向量快取（未實作）— 需補強

**平台管理功能審查結果**：
- ✅ 儀表板、財務、內容審核、審計日誌、成本監控 — 功能完整
- ⚠️ 用戶管理：詳情頁已實作但需驗證、缺「發送通知」按鈕、停權未自動寄信
- ⚠️ Prompt 模板：編輯功能已可用（非「無法編輯」）、缺 model 下拉選單
- ⚠️ 系統設定頁面 6 Tab 過於龐雜，建議拆分

*詳細處理紀錄：`docs/todo-processing-2026-04-17T14-34-13.md`*

### ✅ 11. Feature 32 節點練習模式 + Feature 33 成本監控中心 — 完成於 2026-04-15

**完成範圍**（Feature 32 全部、Feature 33 全部）：

**Feature 32 — 節點練習模式（`32-節點練習模式.feature`）**：
- `backend/app/api/practice.py`：練習題查詢 + 作答 + 進度傳播 3 支 API
- `backend/tests/features/steps/practice/`：完整 step definitions（Given/When/Then）
- `frontend/lib/api/services.ts`：新增 `getNodePracticeQuestions` / `submitPracticeAnswer` 前端 API

**Feature 33 — 成本監控中心（`33-成本監控中心.feature`）**：
- `backend/app/models/ai_usage_ledger.py`：AI 呼叫 token 級用量明細
- `backend/app/models/budget_config.py`：預算設定（四個 scope：AI_ANTHROPIC / AI_GEMINI / AI_VOYAGE / GCP_TOTAL）
- `backend/app/models/budget_alert_log.py`：預算告警日誌
- `backend/alembic/versions/048_add_cost_monitor_tables.py`：Migration 048
- `backend/alembic/versions/049_add_embedding_provider_metadata.py`：Migration 049（Voyage 多 provider 支援）
- `backend/alembic/versions/050_add_gcp_budget_sync_fields.py`：Migration 050（GCP Native Budget 同步欄位）
- `backend/app/repositories/ai_usage_repository.py`
- `backend/app/repositories/budget_config_repository.py`
- `backend/app/repositories/budget_alert_log_repository.py`
- `backend/app/services/cost_monitor_service.py`：成本總覽 + 趨勢圖
- `backend/app/services/budget_service.py`：預算告警觸發 + 功能降級 + 解除停用
- `backend/app/services/gcp_billing_service.py`：GCP BigQuery Billing Export 查詢
- `backend/app/services/gcp_budget_sync_service.py`：GCP Native Budget API 單向同步
- `backend/app/services/voyage_quota_service.py`：Voyage embedding 配額鎖 + 等待佇列
- `backend/app/api/cost_monitor.py`：成本監控 REST API（super_admin 限定）
- `backend/app/core/permissions.py`：`require_super_admin` 依賴注入
- `backend/app/middleware/`：AI Budget 降級 Middleware
- `backend/tests/features/steps/cost_monitor/`：完整 step definitions（Given/When/Then）
- `frontend/app/super-admin/cost-monitor/`：成本監控前端頁面
- `frontend/types/cost-monitor.ts`：前端型別定義
- `project/specs/entity/erm.dbml`：新增 ai_usage_ledger / budget_config / budget_alert_log 三張表 + PENDING_BUDGET_RECOVERY enum + embedding_provider / embedding_model 欄位

**待手動執行：**
- `alembic upgrade head`（migration 048 / 049 / 050）
- 設定 `GCP_BILLING_PROJECT_ID`、`GCP_BILLING_DATASET`、`GCP_BILLING_EXPORT_TABLE`（GCP BigQuery）
- 設定 `GCP_BUDGET_PARENT`（billingbudgets.googleapis.com 同步用）
- BDD 測試驗收（Feature 32 + Feature 33）

*詳細處理紀錄：`docs/todo-processing-2026-04-15T09-00-00.md`*

---

### ✅ 10. LLM 防火牆 + 任務佇列隔離 — 完成於 2026-04-11

**完成範圍**（階段二 1/1、階段三 1/1 剩餘項目）：

**新增/修改檔案：**
- `backend/app/core/llm_firewall.py`：LLM 防火牆（雙層防護：規則引擎 + Llama Guard 客戶端；多租戶感知；OTel 整合；FastAPI exception handler）
- `backend/app/worker.py`：Celery 優先權佇列配置（paid_priority / standard / background / celery 四佇列；task_routes 路由規則；kombu Queue 定義）
- `backend/app/tasks/document_processing.py`：文件解析非同步任務（parse_document_task / ocr_image_task / transcribe_audio_task；方案 → 佇列映射 helper）
- `backend/app/tasks/__init__.py`：新增 document_processing 模組 import
- `backend/app/main.py`：註冊 PromptInjectionError 例外處理器

**待手動執行：**
- LLM 防火牆：設定環境變數 `LLAMA_GUARD_URL`（Llama Guard 推理服務）、`LLAMA_GUARD_API_KEY`
- 佇列隔離：啟動各佇列專屬 Worker（`celery -A app.worker worker -Q paid_priority -c 4`）

**功能說明：**
- LLM 防火牆：規則引擎（即時，零延遲）偵測 Prompt Injection / Jailbreak / 跨租戶攻擊 / PII 萃取；Llama Guard（語意層）可選接入；熔斷器防止服務不穩定；OTel span 記錄威脅事件
- 佇列隔離：B2B + ULTRA_1599 → `paid_priority`；PRO → `standard`；FREE → `background`；方案 → 佇列映射由 `dispatch_*()` helper 自動處理

*詳細處理紀錄：`docs/todo-processing-2026-04-11T09-00-00.md`*

---

### ✅ 9. 基礎設施安全層：欄位加密 + OTel + 限流 + 語意快取 — 完成於 2026-04-09

**完成範圍**（階段二 1/2、階段三 2/3、階段四 1/1）：

**新增/修改檔案：**
- `backend/app/core/field_encryption.py`：Fernet 對稱加密服務（欄位加密、金鑰輪替）
- `backend/app/models/answer.py`：Answer 模型新增 `is_answer_encrypted`、`encrypted_at`、便利方法
- `backend/alembic/versions/041_add_answer_encryption_flag.py`：Migration 041
- `backend/app/core/telemetry.py`：OpenTelemetry 初始化（FastAPI + SQLAlchemy instrument）
- `backend/app/core/rate_limit.py`：多租戶 Token Bucket Middleware（Redis + 記憶體 Fallback）
- `backend/app/services/semantic_cache_service.py`：語意快取服務（Redis + 記憶體 Fallback）
- `backend/app/main.py`：整合 OTel setup + RateLimitMiddleware

**待手動執行：** `alembic upgrade head`（migration 041）；設定 `FIELD_ENCRYPTION_KEY`、`REDIS_URL`、`OTEL_ENABLED=true`

**未完成項目**（需外部基礎設施）：
- 階段二：LLM 防火牆（Llama Guard）
- 階段三：Celery 任務佇列隔離

*詳細處理紀錄：`docs/todo-processing-2026-04-09T09-00-00.md`*

---

### ✅ 8. 資料庫保護與管理（階段一/二部分/四）— 完成於 2026-04-08

**完成範圍**（階段一 4/5、階段二 2/4、階段四 3/3、Feature 檢查）：

**新增/修改檔案：**
- `backend/alembic/versions/038_add_tenants_and_tenant_id.py`：tenants 表 + 7 張業務表 tenant_id + RLS
- `backend/alembic/versions/039_add_hnsw_index_on_embedding.py`：HNSW 向量索引（取代 IVFFlat）
- `backend/app/core/deps.py`：JWT tenant_id DI + `get_tenant_id()`、`get_current_user_with_tenant()`、`set_rls_tenant()`
- `backend/app/core/security.py`：SSRF 防護 utility（黑名單 IP + 白名單域名 + YouTube 專用驗證）
- `backend/app/scripts/purge_tenant_data.py`：租戶資料退場清除腳本（dry-run + GCS 支援）
- `backend/tests/features/environment.py`：BDD 測試環境隔離（TEST_TENANT_ID + _seed_base_data）
- `project/features/31-多租戶安全與資料隔離.feature`：新增 Feature 規格（6 Rules）
- `backend/tests/features/31-多租戶安全與資料隔離.feature`：同步 Feature 測試
- `project/specs/entity/erm.dbml`：新增 tenants 表、tenant_id 欄位、HNSW 索引

**待手動執行：** `alembic upgrade head`（migration 038、039）

**未完成項目**（需外部基礎設施）：
- 階段二：LLM 防火牆（Llama Guard）、欄位級加密
- 階段三：Redis 語意快取、限流、Celery 佇列
- 階段四：OpenTelemetry 全鏈路追蹤

*詳細處理紀錄：`docs/todo-processing-2026-04-08T09-00-00.md`*

---

### ✅ 1. 題目分類 — 完成於 2026-04-02
考古題分析時需進行該科目的題目分類佔比讓模擬考試能有不同難度以及更符合考試趨勢
- 記憶類別 / 理解類別 / 應用類別 / 分析類別 / 評估類別 / 創造類別（Bloom's Taxonomy）

**處理結果**：
- 更新 `project/specs/entity/erm.dbml`：新增 `bloom_category` enum、`questions.bloom_category`、`exams.bloom_distribution`
- 新增 `project/features/18-題目分類與考試趨勢分析.feature`

**待手動執行**：Alembic migration 017、ORM 模型更新、前端圖表

---

### ✅ 2. 考古題爬蟲 — 完成於 2026-04-02
依照台灣證照市場概況與題庫公開程度建立爬蟲 SKILL，優先級：金融 🏆A > 不動產 🏆A > iPAS 🥈B

**處理結果**：
- 新增 `.claude/skills/exam-crawler/SKILL.md`（包含爬蟲策略、Bloom 分類 Prompt、標準輸出 JSON schema）

**待手動執行**：實作 `backend/scripts/crawlers/` 爬蟲腳本、管理後台匯入 API

---

*詳細處理紀錄：`docs/todo-processing-2026-04-02T10-00-00.md`*

---

### ✅ 7. Prompt 模板管理 — BDD 測試與前後端實作 — 完成於 2026-04-07

**處理結果：**
- 更新 `backend/app/models/prompt_template.py`：新增 `PromptTemplateV2`、`PromptTemplateVersion`、`PromptAbTest`
- 新增 `backend/alembic/versions/037_create_prompt_templates_v2.py`：建立三張新表
- 新增 `backend/app/repositories/prompt_template_repository.py`
- 新增 `backend/app/services/prompt_template_service.py`（含 A/B 分流邏輯）
- 新增 `backend/app/api/prompt_template.py`（admin + internal 路由）
- 新增 `backend/tests/features/steps/prompt_template/`（完整 step definitions）
- 移除 Feature 30 的 `@ignore @command` 標籤（進入 Green 階段）
- 新增 `backend/app/scripts/seed_prompts.py`（YAML frontmatter 解析 + 同步）
- 新增前端頁面：`/super-admin/prompt-templates/`（列表 + 編輯 + 版本歷史 + A/B 測試）

**待手動執行**：`alembic upgrade head`、BDD 測試驗收、首次 seed 執行

*詳細處理紀錄：`docs/todo-processing-2026-04-07T22-14-10.md`*

---

### ✅ 3. Edu 學生訂閱衝突處置 — 完成於 2026-04-06

Edu 學生若已有個人訂閱方案（PRO_199/PRO_PLUS_399），被機構指派 EDU 後的處置方式。

**決議：** 個人訂閱自動「暫停計費」（suspended），EDU 期間以 EDU 方案權益為主；EDU 結束後個人訂閱自動恢復，下次扣款日從恢復日重算。

**處理結果：**
- 更新 `project/features/08-訂閱管理.feature`：新增「EDU 學生既有訂閱衝突處置」章節（4 個 scenarios）

---

### ✅ 4. Edu 學生邀請信密碼設定流程 — 完成於 2026-04-06

Edu 學生收到邀請信點擊連結後，應先進入密碼設定頁，再完成帳號啟用。

**決議：** 邀請連結導向 `/invite/setup-password?token={token}`，密碼設定完成後帳號啟用並導向儀表板。Token 有效期 72 小時。

**處理結果：**
- 更新 `project/features/01-身分驗證.feature`：新增「EDU 學生邀請啟用流程」章節（5 個 scenarios）

---

### ✅ 6. Prompt 模板管理 — DBML + Feature 規格 — 完成於 2026-04-06

將 17 個 LLM Prompt 模板納入 DB 管理，支援版本控制、回滾、A/B 測試、Seed 同步。

**處理結果：**
- 更新 `project/specs/entity/erm.dbml`：新增 `prompt_category`、`ab_test_status` enum + `prompt_templates`、`prompt_template_versions`、`prompt_ab_tests` 3 張表
- 新增 `project/features/30-Prompt模板管理.feature`：10 個 Rule、20+ 個 Example（權限、CRUD、版本管理、回滾、A/B 測試、Seed 同步、by-plan 支援）
- 同步至 `backend/tests/features/30-Prompt模板管理.feature`

**前置完成項：**
- `project/03_Research_and_Development/03_Prompt_Templates/` 資料夾（17 個模板 .md 檔 + README）

**待手動執行：** Alembic migration、ORM 模型、seed 腳本 (`app.scripts.seed_prompts`)、管理後台 UI

---

### ✅ 5. feature_conflicts.md 決議事項處理 — 完成於 2026-04-06

feature_conflicts.md 中標註需 /titi-commander 評估的衝突項目（衝突1次數限制、衝突4更新時機、衝突7功能確認、問題8雙條件、問題9術語、問題10作答觸發）。

**處理結果：**
- 更新 `docs/feature_conflicts.md`：補全 6 個 CEO 決議
- 詳見 `docs/todo-processing-2026-04-06T01-08-22.md`
