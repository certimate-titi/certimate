# 學習鷹架重構計畫書

**版本**：v1.0（2026-05-08）
**作者**：教育顧問 + CTO + 產品經理
**狀態**：待 CEO / 董事會審查
**預估工期**：5-6 週（依優先級分階段交付）

---

## 0. 為什麼要做這件事

現況問題 — 三個關鍵診斷：

1. **教學設計層面**：takeaway / elaborative / strategy 三類鷹架是「靜態學習素材」，缺檢索練習、迷思警示、間隔複習 → 違反主流學習科學證據（Karpicke retrieval、Bjork desirable difficulty、Sweller cognitive load）
2. **檔案類型層面**：K-06 prompt 是「單一模板套全部檔案類型」。PPT、YouTube、考古題、音訊、DOCX、圖片本應走完全不同的鷹架策略 — 強行統一導致 fluency illusion、學習效益打折
3. **系統整合層面**：scaffold 與 question_candidates、node_mastery 完全分流，學習迴圈斷裂；跨資源連結（同概念在 PDF / 影片 / 試題的對照）完全沒做

**目標**：把鷹架從「文檔註解」升級成「主動學習迴圈」。

---

## 1. 建議方案總覽

### 1.1 教學手法升級（跨檔案類型通用）

| 編號 | 改動 | 教學原理 | 證據強度 |
|------|------|---------|----------|
| E1 | takeaway 改「先檢索觸發、後揭曉」UI | Retrieval Practice (Karpicke) | ★★★★★ |
| E2 | 章節讀完頁面自動帶 2-3 同章節題目 | Testing Effect | ★★★★★ |
| E3 | 新增 `pitfall` 鷹架類別（從考古題錯題反推迷思） | Misconception Correction | ★★★★ |
| E4 | 新增 `advance_organizer` 讀前定錨類別 | Ausubel Subsumption Theory | ★★★ |
| E5 | strategy 加交錯複習提示（跨章節 reference） | Bjork Interleaving | ★★★ |
| E6 | elaborative 盲答結果接 SM-2 / FSRS 排程 | Spaced Repetition | ★★★★（長期） |

### 1.2 檔案類型分流（K-06 拆成模板矩陣）

| file_type / detected_content_type | Prompt 代號 | 鷹架策略 |
|----------------------------------|------------|----------|
| PDF 學習指引 / 教材 | `K-06-study` | 現行三類 + pitfall + advance_organizer |
| PDF 簡報 / PPT / PPTX | `K-06-slides` | per-slide retrieval + narrative-rebuild |
| PDF 考古題 / 試題卷 | `K-06-quiz` | concept-extract + variation-prompt |
| YouTube / MP4 影片 | `K-06-video` | timestamped-retrieval + confusion-marker |
| 音訊（MP3 / Podcast 錄音） | `K-06-audio` | dense-time-takeaway + concept-map |
| DOCX 自製筆記 | `K-06-notes` | challenge + pitfall + gap-detect（不蓋原文） |
| 圖片（公式 / 流程圖 / 手寫） | `K-06-image` | redraw-prompt + concept-extract |

### 1.3 跨資源學習迴圈（差異化價值核心）

| 連結 | 描述 |
|------|------|
| C1 | PDF takeaway ↔ Video timestamp（同概念跨媒材跳轉） |
| C2 | 考古題 ↔ 章節 pitfall（錯題反向定位章節） |
| C3 | 跨資源 pitfall 彙整（同迷思集中一頁） |
| C4 | 同概念多視角對照（PDF / 影片 / 講義並列） |

---

## 2. 優先級與分階段交付

| Phase | Sprint | 內容 | 目標效果 |
|-------|--------|------|----------|
| **P0** | Sprint 1（1 週） | E1 takeaway 檢索 UI + E2 章節題目自動展示 + K-06 prompt 模板矩陣骨架 | 跨類型通用改善、用戶立即有感 |
| **P1** | Sprint 2（1 週） | K-06-video（timestamped）+ K-06-quiz + E3 pitfall 類別 | YouTube 與考古題用戶體驗修正 |
| **P2** | Sprint 3（1.5 週） | K-06-slides + K-06-notes + E4 advance_organizer + E5 interleaving | PPT B2B 場景 + 進階個人化 |
| **P3** | Sprint 4（1.5 週） | 跨資源連結（C1-C4）+ E6 SM-2 排程整合 | 平台差異化價值 |

每個 Sprint 結束須通過 CTO Review + QA 三層驗收 + 教育顧問簽核。

---

## 3. 實作細節（P0 起）

### 3.1 P0 — Sprint 1

#### E1 — takeaway 檢索 UI

**前端**：
- 新增 `ScaffoldRetrievalCard` 元件取代部分 `ScaffoldNotebook` 用法
- 預設摺疊 takeaway 內容、顯示「想想看：{prompt 推導出的問句}」
- 點「揭曉」才展開 + 紀錄 `viewed_at` / `recall_attempted` 至 `node_mastery`

**後端**：
- `resource_scaffolds` 表加欄位 `retrieval_prompt: text`（從 takeaway 反推的問句，預生成）
- `_persist_parsed` 流程：每個 takeaway 多 call 一次小 prompt 產出問句（gemini-2.5-flash 即可）
- 新表 `scaffold_interaction_log`（user_id / scaffold_id / event / timestamp）

**Prompt 改動**：K-06 加一段 output schema field：
```
"retrieval_prompt": "string（讀者讀到該章節前可以先思考的問題，
不可洩漏 takeaway 答案，例：『想想看：AI 治理有哪四大原則？』）"
```

#### E2 — 章節讀完帶題

**後端**：
- 新 endpoint `GET /resources/{id}/chapter/{heading}/practice` 回傳該章節 `question_candidates` 中 source_page 對齊的題（取 2-3 題）
- 章節對齊靠 page range：scaffold.source_page_start / end ↔ question.source_page

**前端**：
- 章節原文閱讀面下方加 `<InlinePractice>` 區塊
- 直接呼叫 `practiceService.startMicroPractice()` 復用既有作答 UI

#### Prompt 模板矩陣骨架

**檔案改動**：
- `project/03_Research_and_Development/03_Prompt_Templates/knowledge/` 新增：
  - `K-06-study.md` ← 現行 K-06_resource_parser_v2.md 改名
  - `K-06-slides.md`、`K-06-quiz.md`、`K-06-video.md` 等（暫先 stub，prompt 內容由教育顧問逐步補完）

**選擇邏輯**（`resource_parse_service._select_prompt`）：
```python
def _select_prompt(resource: Resource) -> str:
    ext = (resource.gcs_path or "").lower().rsplit(".", 1)[-1]
    if ext in ("ppt", "pptx"): return "K-06-slides"
    if ext in ("mp4", "mov", "avi", "mkv", "webm"): return "K-06-video"
    if ext in ("mp3", "wav", "m4a", "flac"): return "K-06-audio"
    if ext in ("docx", "doc"): return "K-06-notes"
    if ext in ("png", "jpg", "jpeg", "webp"): return "K-06-image"
    if resource.youtube_url: return "K-06-video"
    if resource.detected_content_type == "practice_questions": return "K-06-quiz"
    return "K-06-study"
```

---

### 3.2 P1 — Sprint 2 重點

**K-06-video**：
- Gemini multimodal 可直接吃影片 file（YouTube 需先抓 transcript）
- Output schema 多 `start_time_sec` / `end_time_sec` 欄位
- 前端加 `<VideoTimestampJump>`，點 takeaway 直接 seek 影片

**K-06-quiz**：
- prompt 強制要求 `concept_extract` 而不是 takeaway
- detected_content_type=practice_questions 時不寫 `parsed_markdown`，只寫 `concept_extract`
- 變形題（variation）寫入 `question_candidates` 標 `tier=T2 generated_from=<original_qid>`

**E3 pitfall 類別**：
- DBML 加 `ResourceScaffoldType.PITFALL = "pitfall"`
- migration 071 加 enum value
- prompt 從考古題錯題分布反推（需要該科目至少 50 題以上才能跑統計）

---

### 3.3 P2 / P3 概述

P2 重點是 PPT-aware（B2B 機構導入用）+ DOCX-aware（進階個人筆記）。
P3 重點是 cross-resource graph（最難、最差異化）+ SM-2 排程。

詳細設計留待 P0/P1 完工驗收後重新評估（可能依使用者數據再調整）。

---

## 4. 預期困難與風險

### 4.1 LLM 成本失控

| 項目 | 風險 | 緩解 |
|------|------|------|
| E1 retrieval_prompt 額外 call | 每章節多 1 次 Flash call → 成本增 ~5% | 用 Gemini Flash（單價低 5×）+ 一次回 30 條 batch |
| E3 pitfall 從考古題反推 | 需要全題庫掃，每科目可能 50-100 題 input | 每科目跑 1 次後快取，不隨資源上傳重算 |
| C1-C4 跨資源 embedding | embedding 對齊需要全文 chunk 對照 | 復用既有 voyage embedding，不再算 |

### 4.2 Prompt 路由的「灰色地帶」

`detected_content_type` 由 LLM 自判，準確率約 85-90%。
- 簡章型 PDF 可能被誤判成 `study_guide` → 跑了不該跑的 takeaway
- 「PDF 內含部分試題的學習指引」（mixed）— 怎麼處理？

**緩解**：
- 加「使用者上傳時自選分類」UI（預設 auto，但允許人工覆寫）
- 後端保留 `manual_content_type_override` 欄位

### 4.3 影片 / 音訊 transcript 對齊

- YouTube：yt-dlp 抓字幕，但中文影片字幕常缺；fallback 跑 Whisper 自動轉錄（成本高）
- 上傳影片：直接餵 Gemini multimodal，但 token 限制下要切片（每片 5-10 分鐘）
- 時間戳：Gemini 回的時間戳格式 `[MM:SS]` 跟 yt-dlp / Whisper 的浮點秒不一致 → 需統一 normalizer

### 4.4 schema migration 影響歷史資源

| 變更 | 影響 |
|------|------|
| `resource_scaffolds.retrieval_prompt` 加欄位 | 歷史資源此欄為 NULL，UI 需 fallback |
| `ResourceScaffoldType` 加 `pitfall` / `advance_organizer` 等 enum value | DB enum 加值不影響舊資料 |
| `scaffold_interaction_log` 新表 | 純新增，零風險 |
| `K-06` 改 prompt | 歷史資源**不重跑**（要重跑使用者得手動觸發 reparse） |

**決策題**：要不要 backfill？
- 不 backfill：節省成本但歷史資源體驗較差
- 全 backfill：成本高（單檔 ~$0.5 USD × 1000+ 檔案 = $500+）
- 分批 backfill：使用者下次點該資源時自動重跑（lazy backfill）— **推薦**

### 4.5 與既有系統的整合衝突

| 現有元件 | 衝突點 | 處理 |
|---------|-------|------|
| `ScaffoldNotebook.tsx` / `ScaffoldMaterial.tsx` / `ScaffoldReplayCard.tsx` | 三類鷹架的 UI 已固化 | 新類型走新元件，三舊元件不動 |
| `question_candidates` 表 | 與 scaffold 分流 | E2 用 page-range JOIN，不改表結構 |
| `node_mastery` 表 | 目前只記節點答題，不記 scaffold 互動 | 新增 `scaffold_interaction_log` 表 |
| `resource_scaffolds.sequence_index` 全資源共用 | 多類型 / 多媒材下會錯亂 | 加 `template_code: str`（K-06-study / K-06-video）區分 |
| 前端 `/practice` 頁 | 目前不感知 scaffold | E2 章節題透過新 endpoint 餵入，不改 /practice 頁 |
| BDD `resource_parse.feature` | 預期固定 30 條 scaffolds | 改成「至少 N 條 by template」+ 各 template 個別 scenario |

### 4.6 PPT / DOCX 的解析失真

- PPT 用 Gemini multimodal 吃，但投影片視覺布局丟失（圖文相對位置）
- DOCX 通常已是純文字 + 表格 → 跟 PDF 差距小，主要差在 prompt 策略
- 風險：**使用者期待「我的 PPT 看起來怎樣 markdown 就怎樣」** → 須在 UX 明確說明「擷取為文字版重點，原檔可下載對照」

---

## 5. 與現有系統整合的具體影響面

### 5.1 後端

```
backend/app/
├── services/
│   ├── resource_parse_service.py              # P0 改 _select_prompt + 模板矩陣
│   ├── prompt_template_service.py             # 復用現有，不動
│   └── scaffold_interaction_service.py        # P0 新增
├── models/
│   ├── resource_scaffold.py                   # P0 加欄位 + P1 加 enum value
│   └── scaffold_interaction_log.py            # P0 新增
├── api/
│   ├── resource_parse.py                      # P0 加 retrieval log endpoint
│   └── practice.py                            # P0 加 chapter practice endpoint
└── alembic/versions/
    └── 071_scaffold_redesign_p0.py            # 加欄位 + 新表
```

### 5.2 前端

```
frontend/
├── components/
│   ├── ScaffoldRetrievalCard.tsx              # P0 新增
│   ├── ScaffoldNotebook.tsx                   # P0 改用 retrieval card
│   ├── InlinePractice.tsx                     # P0 新增
│   ├── VideoTimestampJump.tsx                 # P1 新增
│   └── PitfallCard.tsx                        # P1 新增
└── lib/api/services.ts                        # P0 加 chapter practice / scaffold interaction APIs
```

### 5.3 Prompt 模板

```
project/03_Research_and_Development/03_Prompt_Templates/knowledge/
├── K-06_resource_parser_v2.md → K-06-study.md  # P0 改名
├── K-06-slides.md                              # P2
├── K-06-quiz.md                                # P1
├── K-06-video.md                               # P1
├── K-06-audio.md                               # P3
├── K-06-notes.md                               # P2
└── K-06-image.md                               # P3
```

### 5.4 BDD Feature 與測試

- 既有 `project/features/02-資源上傳.feature` 須增加每檔案類型的 Scenario
- 新增 `project/features/35-學習鷹架檢索練習.feature`（P0）
- 教育顧問會簽：每個 Scenario 須附「教學原理對應」段落

### 5.5 資料庫 migration（按 sprint）

| Migration | 內容 |
|-----------|------|
| 071_scaffold_redesign_p0 | resource_scaffolds 加 retrieval_prompt + template_code；新表 scaffold_interaction_log |
| 072_scaffold_pitfall_enum | enum 加 pitfall, advance_organizer, concept_extract, narrative_rebuild |
| 073_video_scaffold_timestamps | resource_scaffolds 加 start_time_sec, end_time_sec |
| 074_cross_resource_links | 新表 scaffold_cross_link（P3） |

---

## 6. 必須先解的決策題（送 CEO）

| # | 問題 | 選項 | 教育顧問建議 |
|---|------|------|-------------|
| Q1 | 歷史資源是否 backfill | 全跑 / 不跑 / Lazy | **Lazy（用戶下次讀才重跑）** |
| Q2 | 使用者是否可手動覆寫 detected_content_type | 是 / 否 | **是**（auto 為預設，可改） |
| Q3 | YouTube 字幕缺失時是否自動跑 Whisper | 是（成本 ~$0.1 / 小時）/ 否（要用戶提供 SRT） | **是**，但僅限 PRO+ 方案 |
| Q4 | P0 完成後是否立刻發 changelog | 是 / 等到 P1 一起發 | **立刻發**，retrieval UI 是最大 UX 變更 |
| Q5 | E3 pitfall 類別只給 PRO+ 還是全方案 | 全 / PRO+ | **全方案**（教學基本權利） |
| Q6 | 既有 takeaway 預設是否摺疊（檢索模式） | 摺疊 / 展開 | **摺疊**（新邏輯預設），但加「我已熟悉，全部展開」按鈕 |

---

## 7. 驗收標準（每階段必過）

### 7.1 教育驗收（教育顧問簽核）

- 每類 scaffold 必附「對應的教學原理」說明（Karpicke / Ausubel / Bjork ⋯）
- 隨機抽樣 10 份不同類型資源，鷹架由 2 位老師獨立評分（Kappa > 0.7 視為一致）
- A/B 測試：retrieval UI vs 直接揭曉，留存率與練習正確率對照

### 7.2 工程驗收

- 7 種檔案類型均能跑通完整 pipeline
- 每種類型至少 1 個 BDD Scenario 綠燈
- LLM 成本（每資源平均）增幅 ≤ 30%
- pipeline P95 延遲增幅 ≤ 25%

### 7.3 產品驗收

- 用戶調研 NPS ≥ 50
- 章節讀完率 +15%（vs P0 前 baseline）
- 練習題完成率 +20%

---

## 8. 不做的事（Out of Scope）

- AI 教練即時對話 — 已在 EPIC-040 範圍
- 學習路徑推薦 — 由 mindmap_strength_service 負責
- 自動產學員筆記匯出 — 不在學習鷹架範疇
- 多語系鷹架 — 中英以外暫不支援

---

## 9. 風險矩陣總表

| 風險 | 機率 | 衝擊 | 緩解 |
|------|------|------|------|
| LLM 成本爆 | 中 | 高 | Flash 替代 + batch + lazy backfill |
| 用戶反彈「為什麼我的 PPT 變這樣」 | 中 | 中 | 上傳時提示說明 + 保留原檔下載 |
| Prompt 路由判錯（mixed PDF） | 高 | 中 | 用戶可手動覆寫 |
| 跨資源連結品質低 | 高 | 中 | P3 才做，先不擋主線 |
| BDD 測試重做 fixture 工作量大 | 中 | 中 | 每類型只做 1 happy path + 1 error case |
| 教育顧問與工程進度不同步 | 高 | 高 | 每 Sprint Day 1 必過教育顧問簽核 |

---

## 10. 下一步動作

1. CEO 簽核本計畫書（特別是第 6 節決策題）
2. 教育顧問補完 P0 階段三個新元件 / 兩個 prompt schema 的具體內容
3. CTO 排 Sprint 1（建議 2026-05-12 起跑）
4. 產品經理把 E1 / E2 寫成 Feature File
5. QA 架構師預先設計 A/B 測試度量

---

**附錄參考**：
- 教育顧問評估原稿：對話紀錄 2026-05-08
- K-06 現行 prompt：[K-06_resource_parser_v2.md](../project/03_Research_and_Development/03_Prompt_Templates/knowledge/K-06_resource_parser_v2.md)
- `resource_scaffolds` ORM：[resource_scaffold.py](../backend/app/models/resource_scaffold.py)
- 相關 EPIC：EPIC-035（資源解析）、EPIC-040（AI 教練）
