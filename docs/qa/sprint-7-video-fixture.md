# Sprint 7 T55 — VideoTimestampJump 驗證 fixture

雲端 QA 複測影片 viewer 時注入測試資料用。

## 注入 SQL

```sql
-- 假設 user_id, subject_id 已存在
INSERT INTO resources(id, user_id, subject_id, name, type, status, scope, gcs_path, parsed_markdown, created_at)
VALUES(gen_random_uuid(), :user_id, :subject_id, '測試影片講座.mp4', 'video', 'COMPLETED', 'personal', 'https://your-cdn.com/test.mp4', '影片摘要', NOW())
RETURNING id;  -- 取 video_resource_id

-- 4 個 timestamped scaffolds
INSERT INTO resource_scaffolds(id, resource_id, chapter_heading, type, content, retrieval_prompt, template_code)
VALUES
  (gen_random_uuid(), :video_resource_id, '00:32-02:15 AI 三層級分類', 'takeaway',
   'AI 依功能分為 ANI / AGI / ASI 三層級。商業應用幾乎都是 ANI（如語音助理、推薦系統）。',
   '想想看 — 講者提到的 AI 三層級分類是什麼？哪一類最常見？', 'K-06-video'),
  (gen_random_uuid(), :video_resource_id, '12:34-15:00 No-code 平台選擇 6 大因素', 'takeaway',
   'Bubble.io 演示：30 秒做一個註冊表單。Low-code 與 No-code 的差別在於是否寫程式。',
   '想想看 — Bubble.io 演示了什麼？No-code 平台選擇要看哪些因素？', 'K-06-video'),
  (gen_random_uuid(), :video_resource_id, '25:30-27:00 AI 治理風險評估', 'takeaway',
   'AI 治理四大原則：公平、透明、安全、問責。EU AI Act 將 AI 應用分為四個風險等級。',
   '想想看 — AI 治理的四大原則？EU AI Act 的風險分級框架？', 'K-06-video'),
  (gen_random_uuid(), :video_resource_id, '01:45 ChatGPT 不是 AGI', 'pitfall',
   '⚠️ 講者強調：常被誤解 ChatGPT 是 AGI，其實仍屬 ANI（專注語言生成單一任務）。',
   NULL, 'K-06-video');
```

## 驗證項

1. 開啟 `/library/view/watch?docId={video_resource_id}&subjectId={subject_id}`
2. 右側「時間戳重點」清單應出現 4 條，按時間排序：
   - `0:32` AI 三層級分類（takeaway 📌 emerald）
   - `1:45` ChatGPT 不是 AGI（pitfall ⚠️ rose）
   - `12:34` No-code 平台選擇 6 大因素
   - `25:30` AI 治理風險評估
3. 點任一時間戳項目 → video.currentTime 設為對應秒數 + 自動播放（需真實 .mp4 URL）
4. 影片底部章節重點區：3 takeaway RetrievalCard + 1 PitfallAlert

## 本地驗證紀錄（2026-05-09 sprint 7 T55）

✅ 4 條時間戳正確解析 + 排序（regex 三種格式 MM:SS-MM:SS / MM:SS / HH:MM:SS）
✅ 點擊觸發 onJumpTo（透過 video.currentTime + play）
⚠️ 本地 fixture 用 fake URL `https://example.com/test.mp4` → video element CORS / 404 → 不渲染
   雲端複測需真實 GCS 影片 URL

## 雲端 QA Layer 4 待跑

- 上傳真實 MP4 影片到雲端 ultra@certimate.test
- K-06-video prompt 自動觸發
- 觀察 chapter_heading 自動產出時間戳格式
- 驗證 VideoTimestampJump 點擊 + seek 行為
