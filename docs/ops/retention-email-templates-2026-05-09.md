# CertiMate Retention Email 範本與寄送規則
**Issue E: Email retention 觸發** | 版本：v1.0 | 生效日期：2026-05-09

---

## 1. 概述

本文件定義 CertiMate 四封 retention email 的完整文案、觸發條件、寄送頻率、A/B 測試策略，以及用戶偏好設定架構（PDPA 合規）。

**目標用戶人格**：
- 學生族（18-28 歲，自律差，在意 GPA，怕考試）
- 在職備考族（時間零碎，求效率）

**核心原則**：溫暖但不肉麻、絕不感情勒索、內文 ≤ 150 字、每封信有明確的 CTA 與 exit path。

---

## 2. 四封 Retention Email

### 2.1 [每日複習提醒] Daily Review Nudge

**Trigger ID**: `trigger_daily_review`

**觸發條件**：
```sql
SELECT u.id, u.email, u.display_name
FROM users u
WHERE u.subscription_status IN ('active', 'trial')
  AND u.status = 'active'
  -- SM-2 spaced repetition: 有已經逾期的複習節點
  AND EXISTS (
    SELECT 1 FROM question_stats qs
    WHERE qs.user_id = u.id
      AND qs.next_review_date <= CURRENT_DATE
  )
  -- 今日尚未發過此信
  AND NOT EXISTS (
    SELECT 1 FROM email_send_log esl
    WHERE esl.user_id = u.id
      AND esl.trigger_id = 'trigger_daily_review'
      AND DATE(esl.sent_at) = CURRENT_DATE
  )
ORDER BY u.id
```

**寄送時間與頻率**：
- 每日 08:00 台灣時間（TZ 計算 at time zone 'Asia/Taipei'）
- 每人每天最多寄 1 次
- 24 小時內同一用戶不重複寄送

**Subject Line A/B 版本**：
- **A 版本**（鼓勵式）：「今日有 3 個重點等你複習 ✨」
- **B 版本**（直接式）：「複習時間到：你今天的 3 個任務」

**Preview Text**：
- A 版本：「持續複習，離夢想更近一步」
- B 版本：「5 分鐘快速複習，鞏固考科」

**內文（HTML）**：
```html
<div style="font-family:'Helvetica Neue',sans-serif;max-width:540px;margin:0 auto;padding:32px;background:#f8fafc">
  <table style="width:100%;border-collapse:collapse">
    <tr>
      <td style="padding-bottom:24px">
        <h2 style="color:#1e40af;margin:0;font-size:22px">早安，準備迎接今天的進度？ ✨</h2>
      </td>
    </tr>
    <tr>
      <td style="padding-bottom:16px;color:#475569;line-height:1.6;font-size:15px">
        <p style="margin:0 0 12px 0">
          根據你的學習節奏，今天有 <strong>3 個重點鷹架</strong>已經到達複習時機。
        </p>
        <p style="margin:0">
          只需要花 5-10 分鐘快速複習，就能鞏固考科、提升答題率。備考沒有捷徑，但每一次複習都會累積成你的優勢。
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding:24px 0">
        <a href="{{FRONTEND_URL}}/today"
           style="display:inline-block;padding:12px 32px;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;font-size:15px">
          前往今日任務
        </a>
      </td>
    </tr>
    <tr>
      <td style="padding-top:16px;border-top:1px solid #e2e8f0;color:#64748b;font-size:13px;line-height:1.5">
        <p style="margin:12px 0">
          💡 <strong>提示</strong>：複習時間由 SM-2 演算法自動排程，你可以在帳號設定中調整提醒頻率。
        </p>
      </td>
    </tr>
  </table>
</div>
```

**純文字 Fallback**：
```
早安，準備迎接今天的進度？✨

根據你的學習節奏，今天有 3 個重點鷹架已經到達複習時機。
只需要花 5-10 分鐘快速複習，就能鞏固考科、提升答題率。
備考沒有捷徑，但每一次複習都會累積成你的優勢。

前往今日任務 >> {{FRONTEND_URL}}/today

提示：複習時間由 SM-2 演算法自動排程，你可以在帳號設定中調整提醒頻率。
```

**CTA 按鈕**：
- 文字：「前往今日任務」
- 連結：`{{FRONTEND_URL}}/today`（顯示「今日 3 件事」面板）

**退訂連結**：
- 方式：在 email 底部添加細項的通知偏好切換，或統一 unsubscribe link（見 3.2 節）

**A/B 測試建議**：
- **測試維度**：Subject line A vs B（每週 50/50 split）
- **衡量指標**：開信率、點擊率、複習完成率
- **預期贏家**：B 版本（直接式較易誘發立即行動）

---

### 2.2 [週報摘要] Weekly Report Summary

**Trigger ID**: `trigger_weekly_report`

**觸發條件**：
```sql
SELECT u.id, u.email, u.display_name, wr.id as report_id
FROM users u
INNER JOIN weekly_reports wr ON wr.user_id = u.id
WHERE u.subscription_status IN ('active', 'trial')
  AND u.status = 'active'
  AND u.subscription_plan IN ('PRO_199', 'PRO_PLUS_399', 'ULTRA_1599', 'EDU')
  -- 週報剛建立（或排定在週日 09:00）
  AND DATE(wr.created_at) = CURRENT_DATE
  AND NOT EXISTS (
    SELECT 1 FROM email_send_log esl
    WHERE esl.user_id = u.id
      AND esl.trigger_id = 'trigger_weekly_report'
      AND wr.id = esl.related_resource_id
  )
ORDER BY u.id
```

**寄送時間與頻率**：
- 每週日 09:00 台灣時間
- 每人每週最多寄 1 次
- 週報建立後 30 分鐘內立即寄送（或排定在週日 09:00）
- FREE 方案用戶**不**寄送週報

**Subject Line A/B 版本**：
- **A 版本**（成就感）：「你本週的學習成績單 ✅ — 3 場考試、75% 準度」
- **B 版本**（進度式）：「週報來了！本週進度回顧」

**Preview Text**：
- A 版本：「看看自己這週進步了多少」
- B 版本：「AI 教練為你的本週學習打分」

**內文（HTML）**：
來自 `WeeklyReportService.generate_report_html()`，結構：
1. 問候語（含用戶名）
2. AI 週報摘要（若 LLM 可用，~150 字；否則展示統計表）
3. 下週建議（鼓勵 + 具體行動）
4. CTA 按鈕
5. 底部簽名 + 退訂連結

```html
<div style="font-family:'Helvetica Neue',sans-serif;max-width:560px;margin:0 auto;padding:32px;background:#f8fafc">
  <h2 style="color:#2563eb;margin:0 0 16px 0">CertiMate 學習週報</h2>
  <p style="color:#475569;font-size:15px;margin:0 0 8px 0">嗨 {{DISPLAY_NAME}}，</p>
  <p style="color:#475569;font-size:15px;margin:0 0 24px 0">
    這是你 {{WEEK_RANGE}} 的學習週報。持續學習的你真的很棒！
  </p>
  
  <!-- 若有 AI 摘要 -->
  <div style="background:#f0fdf4;border-left:4px solid #059669;padding:16px;margin:24px 0;border-radius:4px">
    <h3 style="color:#059669;margin:0 0 12px 0">AI 學習教練摘要</h3>
    <div style="color:#374151;line-height:1.6;font-size:14px">{{AI_SUMMARY_HTML}}</div>
  </div>
  
  <!-- 或若無 LLM，展示統計表 -->
  <table style="width:100%;border-collapse:collapse;margin:24px 0">
    <tr style="background:#f1f5f9">
      <th style="padding:10px;text-align:left;border:1px solid #cbd5e1;color:#334155;font-weight:600">項目</th>
      <th style="padding:10px;text-align:center;border:1px solid #cbd5e1;color:#334155;font-weight:600">本週</th>
    </tr>
    <tr>
      <td style="padding:10px;border:1px solid #e2e8f0">學習天數</td>
      <td style="padding:10px;text-align:center;border:1px solid #e2e8f0">{{STUDY_DAYS}}</td>
    </tr>
    <tr style="background:#f8fafc">
      <td style="padding:10px;border:1px solid #e2e8f0">測驗次數</td>
      <td style="padding:10px;text-align:center;border:1px solid #e2e8f0">{{EXAMS_TAKEN}}</td>
    </tr>
    <tr>
      <td style="padding:10px;border:1px solid #e2e8f0">題目作答</td>
      <td style="padding:10px;text-align:center;border:1px solid #e2e8f0">{{QUESTIONS_ANSWERED}}</td>
    </tr>
    <tr style="background:#f8fafc">
      <td style="padding:10px;border:1px solid #e2e8f0">平均答題率</td>
      <td style="padding:10px;text-align:center;border:1px solid #e2e8f0;color:#059669;font-weight:600">{{ACCURACY}}%</td>
    </tr>
  </table>
  
  <h3 style="color:#059669;margin:24px 0 12px 0">下週建議</h3>
  <p style="color:#475569;font-size:14px;line-height:1.6;margin:0">
    保持你的學習節奏！每天一點點進步都會累積成大成就。如果有題目卡住，別忘了找 AI 教練聊聊，她會幫你破除迷思。
  </p>
  
  <div style="margin:24px 0">
    <a href="{{FRONTEND_URL}}/dashboard"
       style="display:inline-block;padding:12px 32px;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;font-size:15px">
      檢視詳細進度
    </a>
  </div>
  
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0">
  <p style="color:#6b7280;font-size:12px;margin:0">
    CertiMate 團隊 — 讓備考更聰明<br>
    <a href="https://certimate.app" style="color:#2563eb;text-decoration:none">certimate.app</a>
  </p>
</div>
```

**CTA 按鈕**：
- 文字：「檢視詳細進度」
- 連結：`{{FRONTEND_URL}}/dashboard`

**退訂連結**：見 3.2 節

**A/B 測試建議**：
- **測試維度**：寄送時間（週日 09:00 vs 週一 09:00）
- **衡量指標**：開信率、點擊率、週後续登入率
- **預期贏家**：週日早晨（用戶更可能檢視新週的規劃）

---

### 2.3 [連勝即將斷氣] Streak About to Break

**Trigger ID**: `trigger_streak_warning`

**觸發條件**：
```sql
SELECT u.id, u.email, u.display_name, s.current_streak
FROM users u
INNER JOIN streaks s ON s.user_id = u.id
WHERE u.subscription_status IN ('active', 'trial')
  AND u.status = 'active'
  -- 至少 3 天連勝
  AND s.current_streak >= 3
  -- 今日 22:00 後尚未登入
  AND (
    u.last_login_at < CURRENT_DATE::timestamptz + '22:00:00'::interval
    OR u.last_login_at < CURRENT_DATE::timestamptz
  )
  -- 昨日登入過（確保是活躍用戶）
  AND u.last_login_at >= CURRENT_DATE::timestamptz - INTERVAL '1 day'
  -- 今日尚未發過此信
  AND NOT EXISTS (
    SELECT 1 FROM email_send_log esl
    WHERE esl.user_id = u.id
      AND esl.trigger_id = 'trigger_streak_warning'
      AND DATE(esl.sent_at) = CURRENT_DATE
  )
ORDER BY s.current_streak DESC, u.id
```

**寄送時間與頻率**：
- 每日 22:00 台灣時間
- 每人每日最多寄 1 次
- 連勝中斷後自動停止寄送此信

**Subject Line A/B 版本**：
- **A 版本**（危急感）：「⏰ 你的 5 天連勝即將斷掉！」
- **B 版本**（激勵式）：「再登入一次，保住你的連勝記錄」

**Preview Text**：
- A 版本：「只需 2 分鐘，守住你的成就」
- B 版本：「你已經 5 天沒中斷，今晚再加油」

**內文（HTML）**：
```html
<div style="font-family:'Helvetica Neue',sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#fffbeb">
  <div style="background:#fef3c7;border:2px solid #f59e0b;border-radius:8px;padding:16px;margin-bottom:24px;text-align:center">
    <p style="margin:0;color:#92400e;font-size:16px;font-weight:600">
      🔥 你的 <span style="font-size:18px">{{STREAK_DAYS}}</span> 天連勝
    </p>
  </div>
  
  <h2 style="color:#b45309;margin:0 0 12px 0;font-size:20px">別讓連勝在今晚斷掉</h2>
  
  <p style="color:#475569;font-size:15px;line-height:1.6;margin:0 0 16px 0">
    你已經{{STREAK_DAYS}}天沒中斷了，這是一項很棒的成就！
    在備考的馬拉松中，一致性就是超能力。
  </p>
  
  <p style="color:#475569;font-size:15px;line-height:1.6;margin:0 0 24px 0">
    只需要登入 CertiMate，花個 2-5 分鐘做一道題目或複習一個重點，
    就能把連勝延續到明天。你做得到！
  </p>
  
  <div style="background:#ecfdf5;border-left:4px solid #10b981;padding:12px;margin:24px 0;border-radius:4px">
    <p style="margin:0;color:#065f46;font-size:13px">
      <strong>小知識</strong>：連勝到達 7 天、30 天、100 天時，你會解鎖特殊徽章並獲得額外 XP 加成！
    </p>
  </div>
  
  <a href="{{FRONTEND_URL}}/today"
     style="display:inline-block;padding:12px 32px;background:#dc2626;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;font-size:15px;margin:24px 0">
    立即登入，保住連勝
  </a>
  
  <p style="color:#6b7280;font-size:12px;margin:24px 0 0 0;line-height:1.5">
    你可以在帳號設定中關閉此提醒。<br>
    此為自動化通知，請勿直接回覆。
  </p>
</div>
```

**純文字 Fallback**：
```
🔥 你的 {{STREAK_DAYS}} 天連勝

別讓連勝在今晚斷掉

你已經{{STREAK_DAYS}}天沒中斷了，這是一項很棒的成就！
在備考的馬拉松中，一致性就是超能力。

只需要登入 CertiMate，花個 2-5 分鐘做一道題目或複習一個重點，
就能把連勝延續到明天。你做得到！

小知識：連勝到達 7 天、30 天、100 天時，你會解鎖特殊徽章並獲得額外 XP 加成！

立即登入，保住連勝 >> {{FRONTEND_URL}}/today

你可以在帳號設定中關閉此提醒。
此為自動化通知，請勿直接回覆。
```

**CTA 按鈕**：
- 文字：「立即登入，保住連勝」
- 連結：`{{FRONTEND_URL}}/today`

**退訂連結**：見 3.2 節

**A/B 測試建議**：
- **測試維度**：Subject line A vs B（每日 50/50 split）
- **衡量指標**：開信率、點擊率、當日重新登入率
- **預期贏家**：A 版本（危急感與時間侷限會促發立即行動）

---

### 2.4 [上傳解析失敗] Parse Failure Alert

**Trigger ID**: `trigger_parse_failure`

**觸發條件**：
```sql
SELECT u.id, u.email, u.display_name, r.id as resource_id, r.name
FROM users u
INNER JOIN resources r ON r.user_id = u.id
WHERE u.subscription_status IN ('active', 'trial')
  AND u.status = 'active'
  -- 解析失敗
  AND r.status = 'FAILED'
  -- 失敗時間在最近 5 分鐘內
  AND r.updated_at >= NOW() - INTERVAL '5 minutes'
  -- 尚未寄過此失敗通知
  AND NOT EXISTS (
    SELECT 1 FROM email_send_log esl
    WHERE esl.user_id = u.id
      AND esl.trigger_id = 'trigger_parse_failure'
      AND esl.related_resource_id = r.id
  )
ORDER BY r.updated_at DESC, u.id
```

**寄送時間與頻率**：
- 實時觸發（解析失敗後 5 分鐘內寄送）
- 每份資源每次失敗寄送 1 次
- 不受時間限制（此為事務型 email，必須寄）

**Subject Line A/B 版本**：
- **A 版本**（協助式）：「我們無法解析你上傳的「{{RESOURCE_NAME}}」— 我們在幫你檢查」
- **B 版本**（直接式）：「⚠️ 上傳失敗：「{{RESOURCE_NAME}}」解析遇到問題」

**Preview Text**：
- A 版本：「別擔心，我們馬上檢查原因」
- B 版本：「不用擔心，我們會幫你解決」

**內文（HTML）**：
```html
<div style="font-family:'Helvetica Neue',sans-serif;max-width:520px;margin:0 auto;padding:32px;background:#fef2f2">
  <h2 style="color:#dc2626;margin:0 0 16px 0">我們遇到一個問題 ⚠️</h2>
  
  <p style="color:#475569;font-size:15px;line-height:1.6;margin:0 0 12px 0">
    你上傳的 <strong>「{{RESOURCE_NAME}}」</strong> 在解析時出現錯誤，
    我們無法順利萃取出學習鷹架。
  </p>
  
  <p style="color:#475569;font-size:15px;line-height:1.6;margin:0 0 24px 0">
    這通常是因為：
  </p>
  
  <ul style="color:#475569;font-size:14px;line-height:1.8;margin:0 0 24px 0;padding-left:20px">
    <li>PDF 檔案受損或格式不支援（建議轉換為標準 PDF）</li>
    <li>影像檔解析度過低（建議 300 DPI 以上）</li>
    <li>檔案超過大小限制（{{MAX_FILE_SIZE}} MB）</li>
    <li>短暫系統問題（我們會自動重試）</li>
  </ul>
  
  <div style="background:#fef3c7;border-left:4px solid #f59e0b;padding:16px;margin:24px 0;border-radius:4px">
    <p style="margin:0;color:#78350f;font-size:14px">
      <strong>建議</strong>：請檢查檔案格式，重新上傳試試。
      如果問題持續，我們已經將此案例回報給技術團隊，會盡快聯繫你。
    </p>
  </div>
  
  <a href="{{FRONTEND_URL}}/resources?error=parse_failure&resource_id={{RESOURCE_ID}}"
     style="display:inline-block;padding:12px 32px;background:#f59e0b;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;font-size:15px;margin:24px 0">
    重新上傳檔案
  </a>
  
  <p style="color:#6b7280;font-size:12px;margin:24px 0 0 0;line-height:1.5">
    我們的客服團隊已經知道這個狀況。<br>
    如有任何疑問，請回覆此信或造訪「幫助中心」。<br>
    此為自動化通知，請勿直接回覆。
  </p>
</div>
```

**純文字 Fallback**：
```
我們遇到一個問題 ⚠️

你上傳的「{{RESOURCE_NAME}}」在解析時出現錯誤，
我們無法順利萃取出學習鷹架。

這通常是因為：
- PDF 檔案受損或格式不支援（建議轉換為標準 PDF）
- 影像檔解析度過低（建議 300 DPI 以上）
- 檔案超過大小限制（{{MAX_FILE_SIZE}} MB）
- 短暫系統問題（我們會自動重試）

建議：請檢查檔案格式，重新上傳試試。
如果問題持續，我們已經將此案例回報給技術團隊，會盡快聯繫你。

重新上傳檔案 >> {{FRONTEND_URL}}/resources?error=parse_failure&resource_id={{RESOURCE_ID}}

我們的客服團隊已經知道這個狀況。
如有任何疑問，請回覆此信或造訪「幫助中心」。
此為自動化通知，請勿直接回覆。
```

**CTA 按鈕**：
- 文字：「重新上傳檔案」
- 連結：`{{FRONTEND_URL}}/resources?error=parse_failure&resource_id={{RESOURCE_ID}}`

**退訂連結**：無（此為事務型 email，用戶必須收）

**A/B 測試建議**：
- **不建議 A/B 測試**（此為事務/通知型，非行銷型）
- 但可以測試「自動重試前通知」vs「重試失敗後通知」的時機

---

## 3. 寄送頻率總表與用戶偏好

### 3.1 四封信的寄送屬性

| Email | 類型 | 寄送時間 | 頻率 | FREE | PRO+ | EDU | 可關 |
|-------|------|---------|------|------|------|-----|------|
| 每日複習提醒 | 行銷型 | 每日 08:00 | 每人每日 1 次 | ❌ | ✅ | ✅ | ✅ |
| 週報摘要 | 行銷型 | 週日 09:00 | 每人每週 1 次 | ❌ | ✅ | ✅ | ✅ |
| 連勝即將斷氣 | 遊戲化型 | 每日 22:00 | 每人每日 1 次 | ✅ | ✅ | ✅ | ✅ |
| 上傳解析失敗 | 事務型 | 即時（失敗後 5 分鐘） | 每資源 1 次 | ✅ | ✅ | ✅ | ❌ |

**說明**：
- **FREE 用戶**：只能收「連勝提醒」和「解析失敗」（事務必要）
- **PRO+ 及 EDU**：所有四封都寄送，且都可在帳號設定中關閉（除了解析失敗）
- **可關**：用戶可在「帳號 > 通知偏好」中切換開關

### 3.2 PDPA 合規：用戶偏好架構

**資料庫欄位** (`users.notification_preferences` JSON 欄位)：
```json
{
  "daily_review_nudge": true,
  "weekly_report": true,
  "streak_warning": true,
  "parse_failure_alert": true,
  "unsubscribe_token": "{{JWT_BASED_TOKEN}}"
}
```

**unsubscribe_token 設計**（防止惡意退訂他人）：
- 格式：HS256 簽名 JWT，包含 user_id + purpose="email_unsubscribe"
- 有效期：永久（或 365 天，允許用戶分享連結給親友）
- 生成時機：用戶首次註冊或首次發出 retention email 時
- 用途：郵件底部「管理偏好」或「一鍵全部取消」連結

**Unsubscribe Link HTML**：
所有四封信底部添加：
```html
<div style="border-top:1px solid #e2e8f0;padding-top:12px;margin-top:24px;color:#6b7280;font-size:11px">
  <p style="margin:0 0 6px 0">
    <a href="{{FRONTEND_URL}}/email-preferences?token={{UNSUBSCRIBE_TOKEN}}"
       style="color:#2563eb;text-decoration:underline">管理我的通知偏好</a> | 
    <a href="{{FRONTEND_URL}}/email-preferences?token={{UNSUBSCRIBE_TOKEN}}&action=unsubscribe_all"
       style="color:#dc2626;text-decoration:underline">取消所有 retention email</a>
  </p>
</div>
```

**用戶偏好設定頁面** (`/email-preferences`)：
- 前端頁面需支援 token 驗證
- 顯示四個獨立開關（除了解析失敗強制開啟）
- 提供「全部取消」按鈕
- 提供「重新訂閱」按鈕

**opt-in 確認流程**（新用戶首次寄送前）：
1. 用戶註冊完成 → 發送「歡迎信」，包含「啟用行銷 email」CTA
2. 用戶點擊 CTA → 設定 `notification_preferences.daily_review_nudge = true`
3. 隔日開始寄送複習提醒

或：首次購買 PRO+ → 自動啟用 `daily_review_nudge` 與 `weekly_report`，並在首份週報後讓用戶確認

---

## 4. A/B 測試計畫

### 4.1 優先級排序

**高度優先** — 預期高 ROI：
1. 每日複習提醒：Subject line A vs B（每週測試 1 次，樣本 n≥100）
2. 連勝警告：Subject line A vs B（每週測試 1 次）

**中度優先** — 可選：
3. 週報：寄送時間（週日 09:00 vs 週一 09:00）
4. 連勝警告：寄送時間（22:00 vs 20:00）

**低度優先** — 維持穩定：
5. 解析失敗：保持當前格式（事務型不建議 A/B）

### 4.2 A/B 測試執行模板

**每日複習提醒 Subject Line A/B**：
```
Start: 每週一 00:00
Duration: 7 天
Sample Size: n ≥ 100（符合條件的活躍用戶）
Split: 50% A / 50% B
Variant A: "今日有 3 個重點等你複習 ✨"
Variant B: "複習時間到：你今天的 3 個任務"

Tracking:
- email_sent_at: timestamp
- email_variant: 'A' | 'B'
- email_open: event in PostHog
- email_click: event in PostHog
- review_completed_24h: 24 小時內複習完成率

Winner Criteria:
- Click rate > 5% ⟹ 改為全量發送
- No clear winner ⟹ 延續測試或均勻分配
```

### 4.3 PostHog 事件設計

**EmailSent 事件**：
```json
{
  "event": "email_sent",
  "user_id": "{{USER_ID}}",
  "email_type": "daily_review | weekly_report | streak_warning | parse_failure",
  "subject_variant": "A | B",
  "subscription_plan": "{{PLAN}}",
  "timestamp": "ISO8601"
}

EmailOpened 事件：
{
  "event": "email_opened",
  "user_id": "{{USER_ID}}",
  "email_type": "...",
  "open_timestamp": "ISO8601"
}

EmailClicked 事件：
{
  "event": "email_clicked",
  "user_id": "{{USER_ID}}",
  "email_type": "...",
  "cta_text": "前往今日任務 | 檢視詳細進度 | 立即登入，保住連勝 | 重新上傳檔案",
  "click_timestamp": "ISO8601"
}

EmailUnsubscribed 事件：
{
  "event": "email_unsubscribed",
  "user_id": "{{USER_ID}}",
  "email_type": "...",
  "reason": "manual | complained | bounced",
  "unsubscribe_timestamp": "ISO8601"
}
```

---

## 5. CTO 工作量估算

### 5.1 最小可上線 MVP（Sprint 8 內完成）

**後端**：
1. 建立 `email_send_log` 表（記錄已寄信紀錄，防重複）
   - 欄位：user_id, trigger_id, email_type, sent_at, related_resource_id
   - 索引：(user_id, trigger_id, sent_at)
   - 估時：2 小時

2. 編寫四個 SQL 查詢，整合入現有 `EmailService`
   - 複習提醒查詢：1 小時
   - 週報查詢：已有（只需驗證）
   - 連勝警告查詢：1 小時
   - 解析失敗查詢：30 分鐘
   - 估時共：3.5 小時

3. 在 `EmailService` 新增四個方法
   - `send_daily_review_nudge(user, pending_count)` 
   - `send_weekly_report(user, report)` — 改用新文案
   - `send_streak_warning(user, streak_days)`
   - `send_parse_failure_alert(user, resource, error_msg)`
   - 估時：2 小時

4. Cloud Scheduler / App Engine 排程任務
   - 08:00 觸發複習提醒（時區計算）：1.5 小時
   - 09:00 觸發週報（已有，驗證即可）
   - 22:00 觸發連勝警告：1.5 小時
   - 實時失敗監聽（Pub/Sub 或定期檢查）：1 小時
   - 估時共：5 小時

5. 單元測試 + 整合測試
   - BDD 步驟定義（4 個 Scenario）：2 小時
   - 估時：2 小時

**前端**：
1. `/email-preferences` 偏好設定頁面
   - 四個 toggle switch（daily_review_nudge, weekly_report, streak_warning）
   - 「全部取消」與「重新訂閱」按鈕
   - unsubscribe_token 驗證
   - 估時：2.5 小時

2. 前端 email 追蹤埋點
   - PostHog tracking 集成（emailSent, emailOpened, emailClicked）
   - Pixel 追蹤開信（在 HTML 中注入 1x1 GIF）
   - 估時：1.5 小時

3. Unsubscribe token 生成與驗證
   - 後端 JWT 生成邏輯
   - 前端 token 解析與頁面初始化
   - 估時：1 小時

**總計 MVP**：
- 後端：17 小時
- 前端：5 小時
- **合計：22 小時（≈ 3 個開發日）**

### 5.2 完整版（Sprint 9 追加功能）

**後端追加**：
1. A/B 測試框架
   - `email_ab_tests` 表與決策邏輯
   - 估時：3 小時

2. 健康分數與流失預警
   - `user_health_score` 計算（7 日活躍度、完成率、訂閱期、客服次數）
   - 估時：2 小時

3. 進階退訂管理（Bounce 與 Complaint 處理）
   - SendGrid Webhook 整合
   - 估時：2 小時

**前端追加**：
1. A/B 測試 UI 控制
   - PostHog Feature Flags 整合
   - 估時：1.5 小時

2. 郵件預覽功能（給 CS 團隊測試新文案）
   - 估時：1.5 小時

**完整版總計**：
- 後端追加：7 小時
- 前端追加：3 小時
- **合計：10 小時（≈ 1.5 個開發日）**

**全部合計**：22 + 10 = 32 小時（≈ 4 個開發日）

---

## 6. 實作檢查清單

### 6.1 後端實作

- [ ] 建立 `email_send_log` migration
- [ ] 實作四個 `send_*()` 方法在 `EmailService`
- [ ] 實作四個觸發查詢（整合 `question_stats`, `weekly_reports`, `streaks`, `resources`）
- [ ] Cloud Scheduler 任務配置（08:00, 22:00 TZ conversion）
- [ ] 實時失敗監聽（Pub/Sub 或定期 Cron Job）
- [ ] unsubscribe_token JWT 生成與驗證邏輯
- [ ] BDD 測試 4 scenarios + 步驟定義
- [ ] 郵件範本 HTML 驗證（不同信箱客戶端相容性）

### 6.2 前端實作

- [ ] `/email-preferences` 頁面建立
- [ ] 四個偏好 toggle 與資料保存邏輯
- [ ] unsubscribe_token 解析與 URL query 處理
- [ ] PostHog 事件埋點（emailSent, emailOpened, emailClicked）
- [ ] 開信 Pixel 追蹤（1x1 GIF 元素）
- [ ] Responsive design（mobile-first）
- [ ] Accessibility 檢查（WCAG 2.1 AA）

### 6.3 QA 與驗收

- [ ] Email 內容相關性：欄位填充是否正確（user 名字、資源名稱等）
- [ ] Email 客戶端相容性測試（Gmail, Outlook, Apple Mail, Yahoo）
- [ ] PostHog dashboard 配置與指標追蹤
- [ ] A/B 測試分組邏輯驗證
- [ ] 退訂連結完整流程測試
- [ ] 時區計算驗證（TW timezone for 08:00 / 22:00）

---

## 7. 文案設計原則

### 7.1 語氣指南

**目標人格**：溫暖、鼓勵、非說教
- ❌ 避免：「你不複習就會考不好」、「再不讀書就死定了」（感情勒索）
- ✅ 使用：「每天一點點進步都會累積」、「你做得到」（正向強化）

**用語禁忌**：
- 禁用「必須」、「一定」、「不能」
- 禁用「最後機會」、「現在或永遠」
- 禁用「別人都在…」（攀比）

**建議用語**：
- 「根據你的學習節奏…」（個人化、尊重）
- 「你已經…」（認可成就）
- 「試試…」（友善建議）
- 「我們幫你…」（夥伴感）

### 7.2 內容長度限制

- Subject line：≤ 60 字元（含 emoji）
- Preview text：≤ 100 字元
- Email body：≤ 150 字（不含表格、list）
- CTA 按鈕文字：≤ 25 字元

---

## 8. 監測指標

### 8.1 關鍵 KPI

| 指標 | 目標 | 測量方式 |
|------|------|---------|
| 開信率 (Open Rate) | ≥ 20% | Email 平台 + Pixel 追蹤 |
| 點擊率 (Click Rate) | ≥ 5% | PostHog + URL parameter |
| 轉化率 (Conversion) | ≥ 10%（執行行動） | 行為追蹤（複習完成、登入） |
| 退訂率 (Unsubscribe) | ≤ 2% | 主動管理偏好 |
| 投訴率 (Complaint) | ≤ 0.1% | Email 平台回報 |
| 重新啟動率 (Reactivation) | ≥ 15%（針對非活躍用戶） | DAU 恢復追蹤 |

### 8.2 次層指標

- 連勝警告：當日重新登入率（A vs B）
- 週報：點擊後 7 日登入率
- 複習提醒：點擊後 24 小時內完成複習的比例

---

## 9. 故障排除與邊界案例

### 9.1 常見問題

**Q: 用戶同時符合多個 trigger，會被轟炸嗎？**
A: 不會。`email_send_log` 記錄以 trigger_id 為單位，每日每人每 trigger 最多 1 次。若同一時間符合多個 trigger（例如 22:00 既有複習也將斷勝），排序發送：事務型 > 遊戲化型 > 行銷型。

**Q: 用戶關掉通知後，改變主意要重新訂閱？**
A: 點擊「重新訂閱」按鈕，更新 `notification_preferences` 即可。下次符合 trigger 時正常寄送。

**Q: 郵件被標記為垃圾怎麼辦？**
A: 
1. 監測 SendGrid Complaint 事件，自動停止對該用戶寄送此 trigger
2. 每月檢查垃圾信回報率，調整 sender reputation
3. 使用 SPF / DKIM / DMARC 認證，提升傳遞率

**Q: 用戶改變時區怎麼辦？**
A: 在 users 表新增 `timezone` 欄位（預設 Asia/Taipei），排程任務以此計算發送時間。

### 9.2 邊界案例

| 情境 | 處理方式 |
|------|---------|
| 用戶帳號被刪除 | email_send_log 保留作歷史紀錄；排程查詢自動 skip |
| 用戶 email 變更 | old_email 的 log 保留；new_email 重新開始追蹤 |
| 用戶轉換訂閱方案 | 若從 PRO+ 降至 FREE，停止「複習提醒」與「週報」但續續寄「連勝警告」 |
| Email 發送失敗（SMTP timeout） | 記錄 email_send_log.status='failed'；30 分鐘後自動重試 1 次 |
| 郵件客戶端不支援 HTML | 自動降級至純文字版本（已在 EmailService._send() 實作） |

---

## 10. 交付清單

**文件**：
- [ ] 本檔案：retention-email-templates-2026-05-09.md（CS 與 CTO 參考）
- [ ] Migration SQL：email_send_log 表定義
- [ ] EmailService 新方法文件
- [ ] PostHog 事件架構文件

**程式碼**：
- [ ] `backend/app/services/email_service.py` — 四個新方法
- [ ] `backend/app/api/email_preferences.py` — REST endpoint
- [ ] `frontend/app/(auth)/email-preferences/page.tsx` — 偏好設定 UI
- [ ] Cloud Scheduler 任務定義（YAML）
- [ ] BDD feature file + step definitions

**測試**：
- [ ] 4 × Scenario (backend + frontend 各 1 個)
- [ ] 單元測試：Email 方法、JWT token 驗證
- [ ] 整合測試：完整觸發流程

---

## 附錄 A：Email 範本變數字典

| 變數 | 格式 | 來源 |
|------|------|------|
| `{{FRONTEND_URL}}` | https://certimate.app | 環境變數 |
| `{{DISPLAY_NAME}}` | "Alice" 或 "alice@example.com" | users.display_name 或 users.email |
| `{{RESOURCE_NAME}}` | "大一微積分筆記.pdf" | resources.name |
| `{{RESOURCE_ID}}` | UUID | resources.id |
| `{{STREAK_DAYS}}` | 5, 7, 30 | streaks.current_streak |
| `{{WEEK_RANGE}}` | "04/28 ~ 05/04" | weekly_reports 日期 |
| `{{STUDY_DAYS}}` | 6 | 計算：exams with submitted_at in week |
| `{{EXAMS_TAKEN}}` | 3 | count(exams) |
| `{{QUESTIONS_ANSWERED}}` | 45 | sum(exams.total_questions) |
| `{{ACCURACY}}` | 75 | 計算：correct_count / total_questions |
| `{{AI_SUMMARY_HTML}}` | HTML block | LLM 生成的週報摘要 |
| `{{UNSUBSCRIBE_TOKEN}}` | JWT string | JWT 簽名，包含 user_id |
| `{{MAX_FILE_SIZE}}` | "50" | plan_quotas.max_file_size_mb |

---

## 附錄 B：Email 審核檢查清單（CS 驗收）

寄送任何 retention email 前，驗證：

- [ ] Subject line 無打字錯誤，emoji 正確渲染
- [ ] Preview text 有意義（非截斷）
- [ ] 收件人名字正確填入
- [ ] CTA 連結指向正確頁面（?token=, ?resource_id= 等參數）
- [ ] 退訂連結可點擊且有效
- [ ] HTML 在三款信箱客戶端相容（Gmail, Outlook, Apple）
- [ ] 純文字版本無亂碼
- [ ] 品牌色彩、logo 符合視覺規範
- [ ] 無競品提及（內容中立）
- [ ] 符合 PDPA 與當地法規（台灣電子商務等）

---

**文件完成日期**：2026-05-09  
**最後更新者**：CertiMate 客戶成功經理 (TiTi)  
**下一次審核**：2026-06-09（月度 A/B 測試結果報告）
