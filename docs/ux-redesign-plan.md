# CertiMate UX 全面重設計計畫書

**版本**：v1.0（2026-05-08）
**作者**：前端工程師 + 教育顧問 + 設計師三方共審
**對應**：[scaffold-redesign-plan.md](scaffold-redesign-plan.md) — 學習鷹架重構技術計畫
**狀態**：待 CEO + 董事會審查

---

## 0. 為什麼要做整體 UX 重設計

學習鷹架重構（K-06 prompt 模板矩陣 + 7 種檔案類型 + 跨資源連結）是後端教學設計層的升級。
但若前端只在現有「圖譜為主 + 章節閱讀為輔」的框架下打補丁，會撞牆三次：

1. **教學設計**：retrieval-first UX 需要全頁面節奏改變，不能塞進現有閱讀面板
2. **檔案類型**：影片需要時間軸主導、PPT 需要投影片網格、考古題需要錯題解析模板 — 一個 viewer 撐不住
3. **技術架構**：`knowledge/page.tsx` 1,222 行巨石、`ScaffoldMaterial/Notebook/ReplayCard` 各自 fetch、`centerView` 狀態耦合 — 再加 4-5 個鷹架類別會徹底失控

**結論**：趁鷹架重構順勢做整體 UX 重設計。重設計範圍涵蓋：上傳 / 資源庫 / 閱讀 / 鷹架互動 / 章節練習 / 跨資源檢視 / 儀表板。

---

## 1. 三方視角現況評估

### 1.1 前端工程師視角（技術可行性）

**盤點結論**（詳見前端工程師獨立報告）：

| 元件 | 行數 | 痛點 |
|------|------|------|
| `frontend/app/knowledge/page.tsx` | **1,222** | 36 useState / 8 useEffect / 圖譜 + 文件 + 鷹架 + AI 教練全擠一頁 |
| `frontend/components/ScaffoldMaterial.tsx` | 285 | 各自 fetch、無協調層 |
| `frontend/components/ScaffoldNotebook.tsx` | 184 | 同上 |
| `frontend/components/ScaffoldReplayCard.tsx` | 106 | 同上 |
| `frontend/app/dashboard/page.tsx` | 702 | 上傳入口、進度摘要混雜 |

**前三高重構成本**：
1. knowledge/page.tsx 巨石化 — **18 hr**
2. 章節閱讀無獨立 URL（`centerView` 狀態耦合）— **14 hr**
3. Scaffold 元件重複 API 呼叫 — **8 hr**

**前端兩大建議**：
- **A**: 章節閱讀獨立子路由 `/knowledge/reading?docId=&subjectId=`
- **B**: 抽 `useKnowledgePageState` + `useNodeScaffoldData(nodeId)` 兩個 hook

### 1.2 教育顧問視角（學習科學）

**核心診斷**：現況是「**靜態素材瀏覽器**」，不是「**主動學習迴圈**」。

| 學習科學原則 | 現況支援度 | 缺口 |
|-------------|-----------|------|
| Retrieval Practice (Karpicke) | ★ 完全沒做 — takeaway 直接公佈答案 | E1 檢索觸發 UI |
| Testing Effect | ★★ 有 question_candidates 但與章節脫鉤 | E2 章節讀完帶題 |
| Misconception Correction | ★ 完全沒做 | E3 pitfall 類別 |
| Advance Organizer (Ausubel) | ★ 完全沒做 — 只有讀後總結 | E4 讀前定錨 |
| Interleaving (Bjork) | ★ 章節獨立、無交錯 | E5 跨章節 reference |
| Spaced Repetition | ★★ 有 node_mastery 但不接 scaffold 互動 | E6 SM-2 排程 |
| Cognitive Load (Sweller) | ★★★ 介面清爽但 scaffold 數量易過載 | 章節讀完才彈鷹架（lazy） |

**教育顧問三大要求**：
1. **每個鷹架的「揭曉前必經一次主動回想」** — UX 預設摺疊
2. **章節閱讀 + 練習 + 鷹架互動必同頁** — 不要切走頁面
3. **跨資源同概念可跳轉** — PDF takeaway ↔ Video timestamp

### 1.3 設計師視角（資訊架構與視覺）

**核心診斷**：當前資訊架構是「**科目 → 圖譜中心**」，但使用者真正需要的是「**目標 → 學習活動**」。

**現況 IA 問題**：
- 進入 `/knowledge` 看到的是圖譜，但 80% 使用者上來是想「繼續讀上次的章節」或「該複習什麼」
- 圖譜是知識探索工具，不是學習主入口；卻被當成首頁
- 上傳資源在 `/dashboard`、閱讀在 `/knowledge`、練習在 `/practice`、複習在 `/knowledge/wrong-answers` — **學習動線割裂**
- 多檔案類型沒有視覺差異化（影片、PPT、PDF、音訊在資源列表長一樣，沒 thumbnail / 進度條 / 時長）

**設計師三大主張**：
1. **重劃 IA 從「視圖中心」變「活動中心」**：閱讀 / 練習 / 複習各自是頂層動詞
2. **檔案類型差異化視覺語言**：thumbnail / icon / 進度指示 / 時長 / 元數據各自設計
3. **學習節奏視覺化**：跟休息提示、Sprint 衝刺、Streak 整合，不是孤立的訂閱資訊

---

## 2. 重設計核心原則（三方共識）

```
P1. Activity-First, Not View-First
   首頁是「現在該學什麼」，不是「這科有什麼」

P2. Retrieval Before Reveal
   所有 takeaway / pitfall 預設摺疊，揭曉前必經一次主動回想

P3. One Concept, Many Sources
   同一個概念在 PDF / 影片 / 試題的不同呈現可一鍵切換

P4. File-Type Aware UI
   PPT / Video / Audio / Quiz 各有專屬 viewer 與 scaffold layout

P5. Progressive Disclosure
   章節級鷹架 lazy load，不一次塞 90 條給用戶

P6. Stateful URLs
   章節 / 鷹架 / 練習都可深連結（瀏覽器返回鍵正確）

P7. Visual Hierarchy: Activity > Content > Tool
   學習活動（讀／練／複習）視覺層級最強
   內容素材（章節 / 題目）次之
   輔助工具（圖譜 / 設定）最弱
```

---

## 3. 全新資訊架構（IA）

### 3.1 路由結構（變更前後對照）

| 現況 | 重設計 | 用途 |
|------|--------|------|
| `/dashboard` | `/`（學習首頁）| 今日活動 / 衝刺 / Streak / 上傳入口 |
| `/knowledge` | `/library/[subjectId]` | 資源庫（按科目）— 列表 + thumbnail + 類型 filter |
| 無 | `/library/[subjectId]/reading?docId=&chapter=` | 章節閱讀（獨立 URL，可分享）|
| 無 | `/library/[subjectId]/concept/[conceptId]` | 概念中心頁（跨資源同概念彙整） |
| `/knowledge/mindmap` | `/library/[subjectId]/map` | 知識圖譜（從輔助工具入口進入） |
| `/practice` | `/study/practice` | 練習活動 |
| `/exam/setup` | `/study/exam` | 模擬測驗 |
| `/knowledge/wrong-answers` | `/study/review` | 複習錯題 |
| `/account/resource-library` | `/library/all` | 跨科目所有資源 |

### 3.2 主要動線重設計

```
今日學習動線（重設計後）
─────────────────────────
1. 開 / 看到「今日 3 件事」：
   - 「繼續讀第 3 章」(20 min) ← 上次中斷處
   - 「複習 5 題錯題」(10 min) ← 遺忘曲線提醒
   - 「Sprint 模擬測驗」(30 min) ← 距考試 N 天

2. 點「繼續讀第 3 章」
   → /library/{sid}/reading?docId={did}&chapter=3.1
   → 頁首顯示「第 3.1 節 No-code 概念 - 預計 20 分鐘」
   → 章節讀前出現 advance_organizer：「想想看：No-code 和 Low-code 差在哪？」
   → 摺疊狀態，可選擇「先看答案」或「先想再看」
   → 內文閱讀（含圖、表、KaTeX）
   → 章節結尾：retrieval takeaway × 3（摺疊）→ pitfall × 1 → 自動帶 2 題練習

3. 章節練習答完
   → SM-2 紀錄寫入 node_mastery
   → 提示「明天繼續第 3.2 節 / 直接跳第 4 章 / 看跨章節對照」

4. 想看圖譜時點工具列「🗺️ 知識圖譜」
   → /library/{sid}/map
   → 從輔助工具入口進入，不再是首頁
```

---

## 4. 跨檔案類型 UX 模式

### 4.1 資源庫列表（重設計）

每種檔案類型有專屬視覺語言：

```
┌────────────────────────────────────────────────────────┐
│ 📄 PDF 學習指引   AI應用規劃師-科目1.pdf                │
│ ┌──┐ 62 頁 · 已讀 12/62 · 30 章節 · 90 鷹架            │
│ │📕│ ▓▓░░░░░░░░ 19%                              [讀]  │
│ └──┘ 上次讀到：第 3 章 No-code 概念                      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ 🎬 影片  iPAS 應用規劃師講解.mp4                        │
│ ┌──┐ 45:32 · 已看 12:34 · 6 段重點 · 3 個迷思警示       │
│ │▶ │ ▓▓▓░░░░░░░ 27%                              [看]  │
│ └──┘ 上次看到：12:34 「No-code 平台選擇 6 大因素」      │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ 📊 簡報  ai-fundamentals.pptx                          │
│ ┌──┐ 24 張 · 已過 8/24 · 5 條敘述重建任務                │
│ │📊│ ▓▓▓▓░░░░░░ 33%                              [過]  │
│ └──┘ 上次過到：第 8 張「機器學習三類型」                 │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ 🎧 音訊  podcast-genai-2025.mp3                        │
│ ┌──┐ 23:15 · 已聽 0:00 · 含逐字稿 · 12 個概念地圖點     │
│ │🎧│ ░░░░░░░░░░ 0%                                [聽]  │
│ └──┘ 尚未開始                                            │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ ❓ 試題卷  113-3 考古題.pdf                             │
│ ┌──┐ 50 題 · 已答 0/50 · 8 個常見迷思                   │
│ │❓│ ░░░░░░░░░░ 0%                              [作答] │
│ └──┘ 尚未開始                                            │
└────────────────────────────────────────────────────────┘
```

每張卡片必含：
- **類型 icon**（emoji 或 lucide icon）
- **類型專屬元數據**（頁數 / 時長 / 投影片數 / 題數）
- **進度條**（讀過 / 看過 / 答過比率）
- **鷹架 / 迷思 / 概念點數量**
- **上次中斷處** — 學習延續性最重要
- **主行動按鈕**（讀 / 看 / 過 / 聽 / 作答）

### 4.2 各類型 viewer 重設計要點

#### PDF 學習指引 → `/library/{sid}/reading?docId&chapter`
- 左側目錄樹（章節 / 子節）
- 中央內文（markdown 渲染、含圖、KaTeX）
- 右側折疊面板：advance_organizer（讀前）/ takeaway（讀後）/ pitfall / 章節題
- 章節讀完底部 Sticky bar：「下一節」「複習此節」「跨資源對照」

#### YouTube / MP4 影片 → `/library/{sid}/watch?docId&t=`
- 影片播放器置頂、固定（HTML5 `<video>` 或 YouTube embed）
- 右側面板：時間戳重點清單（takeaway / pitfall），點任何一條 → `currentTime = seconds`
- 重點預設摺疊（retrieval-first），用戶手動展開才看答案
- ❌ **不做強制暫停**（過度工程、用戶煩、跨裝置難穩）
- ❌ **不做「看完整支才解鎖」**（侵入感太強）
- 用戶自律：想練 retrieval 自己按 ⭐ 標記點，主動暫停想完再點答案揭曉

#### PPT 簡報 → `/library/{sid}/slides?docId&page=`
- 投影片網格首頁（縮圖 4 列）
- 點任一張進全屏 viewer（左右翻頁）
- 每張下方：slide-retrieval（不是 takeaway）「請補完這張投影片想表達的論述」
- 連續 3 張看完彈出 narrative-rebuild：「把這 3 張連起來重述故事線」

#### 音訊 → `/library/{sid}/listen?docId&t=`
- 上方音訊波形 + 播放控制
- 中央逐字稿（同步高亮當前句）
- 右側 concept-map 預覽（每段對應一個概念節點，可開新分頁畫圖）
- 段落結束彈出 dense-time-takeaway，比影片更密

#### 考古題試題卷 → `/library/{sid}/quiz?docId`
- 一題一頁全屏作答 UI（同 /study/practice）
- 答完才顯示 concept-extract 而非 takeaway
- 自動產 variation 題（一鍵「換個問法」）
- 全卷統計：每題 pitfall + 與哪些章節對應

---

## 5. 關鍵畫面 wireframes

### 5.1 學習首頁 `/`（取代 dashboard）

```
┌──────────────────────────────────────────────────────────────┐
│ TiTi  儀表板  學習庫  練習  AI教練                    Admin S│
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  早安，Simon  ｜距 AI 應用規劃師考試 8 天 ｜🔥 5 天連續        │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  🎯 今日 3 件事（30 分鐘）                                │ │
│  │                                                            │ │
│  │  ⓵ 📖 繼續讀「3.2 生成式 AI 應用領域」     20 分  [開始] │ │
│  │     上次停在「市場價值與影響力」                          │ │
│  │                                                            │ │
│  │  ⓶ ✅ 複習 5 題錯題（依遺忘曲線提醒）        10 分  [開始] │ │
│  │     上次答錯：「No-code 6 大評估因素」                    │ │
│  │                                                            │ │
│  │  ⓷ 📊 Sprint 模擬測驗（25 題）              30 分  [開始] │ │
│  │     建議在 8 天內安排 3 次模擬                            │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  本週節奏（綠豆豆熱力圖）                                       │
│  今 明 一 二 三 四 五                                           │
│  ▓▓ ▓▓ ░░ ░░ ▓▓ ░░ ░░                                          │
│                                                                │
│  快速匯入          學習狀態                                     │
│  ┌──────┐         整體答對率 25% │ 預測及格率 35%              │
│  │ + 上傳 │         能力分佈：                                  │
│  └──────┘          人工智慧基礎概論 ▓▓▓░░░ 50%                 │
│                    生成式 AI 應用 ▓░░░░░ 20%                   │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 章節閱讀頁 `/library/{sid}/reading?docId&chapter`

```
┌──────────────────────────────────────────────────────────────┐
│ ← 學習庫  ｜ AI 應用規劃師-科目2.pdf  ｜ 第 3.1 節 - 第 3 / 30 │
├────────────┬───────────────────────────────────┬─────────────┤
│ 目錄        │  ✦ 想想看（讀前）  [先想再看 ▽]   │ 章節資訊     │
│            │  ─────────────────────────────    │             │
│ 第一章      │  No-code 和 Low-code 在你公司具    │ 預計 12 分   │
│ 第二章      │  體差異會在哪一個流程體現？       │ 9 個鷹架     │
│ ▼ 第三章    │                                   │ 2 個迷思     │
│   ▶ 3.1    │  [先看答案]                        │ 3 題練習     │
│   ▶ 3.2    │                                   │             │
│   ▶ 3.3    │  ──────── 內文 ────────           │ 跨資源對照：  │
│            │                                   │ 🎬 影片 12:34│
│            │  No-code 平台允許非技術用戶通過    │ ❓ 113-3 第8題│
│            │  圖形介面創建應用，而 Low-code     │             │
│            │  平台則為開發者提供視覺化工具⋯     │             │
│            │                                   │             │
│            │  ![圖](FIGURE:p3_i0)               │             │
│            │                                   │             │
│            │  [六大關鍵因素]                    │             │
│            │  1. 目標用戶                        │             │
│            │  2. 功能擴展性                      │             │
│            │  ⋯                                 │             │
│            │                                   │             │
│            │  ──────── 章節結尾 ────────        │             │
│            │                                   │             │
│            │  📌 重點精煉  [想想看 ▽]           │             │
│            │  📌 重點精煉  [想想看 ▽]           │             │
│            │  📌 重點精煉  [想想看 ▽]           │             │
│            │                                   │             │
│            │  ⚠️ 常見迷思  [想想看 ▽]           │             │
│            │                                   │             │
│            │  💭 延伸思考  [回答 →]              │             │
│            │                                   │             │
│            │  ✅ 章節練習（自動帶題）             │             │
│            │  ┌────────────────────────────┐   │             │
│            │  │ 1. 下列何者不屬於 No-code  │   │             │
│            │  │    平台的特點？             │   │             │
│            │  │  (A) ⋯                     │   │             │
│            │  └────────────────────────────┘   │             │
│            │                                   │             │
├────────────┴───────────────────────────────────┴─────────────┤
│  [← 上一節]    [完成此節 ✓]    [跨資源對照]   [下一節 →]      │
└──────────────────────────────────────────────────────────────┘
```

### 5.3 概念中心頁 `/library/{sid}/concept/[conceptId]` ⭐ 新增

```
┌──────────────────────────────────────────────────────────────┐
│  概念：No-code / Low-code 平台選擇                              │
│  你的掌握度 ▓▓▓░░░ 50%（昨天 40% ↑）                            │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  📄 PDF 教材觀點（科目 2 - 3.1 節）                              │
│  ──────────────────────────────────                            │
│  No-code 對應「非技術用戶、視覺化、拖放操作」⋯                  │
│  [前往章節 →]                                                   │
│                                                                │
│  🎬 影片觀點（iPAS 講解.mp4 @ 12:34）                            │
│  ──────────────────────────────────                            │
│  講師示範：用 Bubble.io 30 秒做一個註冊表單                     │
│  [跳到該段 →]                                                   │
│                                                                │
│  ❓ 考古題碰過幾次（113-1 / 113-3 / 114-1 共 5 題）              │
│  ──────────────────────────────────                            │
│  你答對 2 / 5 — 最常錯選 C「目標用戶不重要」                    │
│  ⚠️ 迷思警示：很多人以為 Low-code 就是少寫一點程式，            │
│     其實 Low-code 是「結構不同」，不是「程式量少」               │
│  [複習這 3 題錯題 →]                                            │
│                                                                │
│  💭 延伸思考                                                    │
│  ──────────────────────────────────                            │
│  你公司若導入 No-code，最可能在哪 3 個流程體現差異？             │
│  [展開回答區 →]                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. 互動模式庫（reusable patterns）

### 6.1 RetrievalCard（檢索觸發卡）

```
┌─────────────────────────────────────┐
│ 📌 想想看                            │
│                                       │
│  AI 治理的四大原則是什麼？           │
│                                       │
│  ⏱ 先想 30 秒再看                   │
│  ─────────────────────────────       │
│  [我想完了，看答案 →]                 │
└─────────────────────────────────────┘
        ↓ 點擊「我想完了」
┌─────────────────────────────────────┐
│ 📌 已揭曉                            │
│                                       │
│  AI 治理的四大原則是什麼？           │
│                                       │
│  公平性、透明性、安全性、問責性       │
│                                       │
│  你的回想感覺：                       │
│  [完全沒想到] [想到一半] [完全想到]  │
│                                       │
│  → 寫入 node_mastery，影響 SM-2 排程  │
└─────────────────────────────────────┘
```

### 6.2 PitfallAlert（迷思警示卡）

```
┌─────────────────────────────────────┐
│ ⚠️ 常見迷思                          │
│                                       │
│  很多人以為 Low-code 是「程式量少」  │
│  其實 Low-code 是「程式 + 視覺化」    │
│                                       │
│  💡 Bubble.io 是 No-code，          │
│     OutSystems 是 Low-code           │
│                                       │
│  📊 113-3 考古題第 8 題 32% 學員選錯 │
│  [看那題 →]                          │
└─────────────────────────────────────┘
```

### 6.3 InlinePractice（章節題自動帶入）

章節讀完底部出現 1-3 題，作答後即時 SM-2 寫入。
答錯題自動加入 `/study/review` 待複習清單。

### 6.4 CrossSourceJump（跨資源跳轉）

每個 concept tag 旁附 popover：「同概念在這 3 份資源出現過 → 一鍵切換視角」

---

## 7. 視覺規範升級（補 Design.md）

### 7.1 新增的色彩語意

| 用途 | Token |
|------|-------|
| **檢索卡（未揭曉）** | `bg-amber-50 border-amber-200`（鼓勵思考） |
| **檢索卡（已揭曉）** | `bg-emerald-50 border-emerald-200` |
| **迷思警示** | `bg-rose-50 border-rose-200` + `text-rose-700` |
| **延伸思考** | `bg-indigo-50 border-indigo-200` |
| **跨資源對照** | `bg-purple-50 border-purple-200` |

### 7.2 新增的元件 token

| 元件 | 規範 |
|------|------|
| RetrievalCard 摺疊狀態 | `rounded-2xl border-2 border-dashed border-amber-300 p-4` |
| RetrievalCard 揭曉狀態 | `rounded-2xl border border-emerald-200 bg-emerald-50 p-4` |
| 章節練習 wrapper | `rounded-2xl bg-slate-50 p-5 mt-6` |
| 跨資源對照 popover | `shadow-xl rounded-2xl bg-white p-4 max-w-md` |
| 進度條（resource card）| `h-1.5 rounded-full bg-slate-100` + `bg-emerald-500` 填滿 |

### 7.3 動效節制

| 場景 | 動效 |
|------|------|
| 檢索卡揭曉 | 0.3s ease-out fade + slight slide-down，不可彈跳 |
| 章節練習答對 | Confetti 粒子（已有元件 `Confetti.tsx`），但只在連對 3 題才觸發 |
| 跨資源跳轉 | 0.2s 淡出 → 路由切換 → 0.2s 淡入 |
| 影片時間軸高亮 | 不用動效，只用顏色變化 |

### 7.4 字體層級重新校準

| 場景 | 規範 |
|------|------|
| 章節標題 H2 | `text-xl font-bold text-slate-900` |
| 章節內文 | `text-base text-slate-700 leading-relaxed`（從 `text-sm` 升級，閱讀更舒適） |
| RetrievalCard 問題 | `text-base font-medium text-slate-900` |
| RetrievalCard 答案 | `text-sm text-slate-700` |
| 迷思警示主文 | `text-sm font-medium text-rose-700` |

---

## 8. A11y / RWD 規範

### 8.1 鍵盤操作

| 動作 | 鍵 |
|------|------|
| 章節翻頁 | `[` / `]` |
| 揭曉檢索卡 | `Space`（focus 時） |
| 跳到章節練習 | `g` then `p`（雙鍵組合） |
| 開啟跨資源對照 | `c` |
| 關閉 popover / 全屏退出 | `Esc` |

### 8.2 ARIA 標記

- 檢索卡 `role="region"` + `aria-expanded` 切換
- 影片時間軸點 `role="button"` + `aria-label="跳到 12:34 的重點：No-code 平台選擇"`
- 進度條 `role="progressbar"` + `aria-valuenow / valuemin / valuemax`

### 8.3 RWD 斷點適配

| 斷點 | 章節閱讀頁佈局 |
|------|---------------|
| `< sm` | 單欄（目錄變成抽屜、右側資訊變底部 sheet） |
| `sm-lg` | 雙欄（目錄 + 內文，右側資訊 toggle） |
| `≥ lg` | 三欄（目錄 + 內文 + 右側資訊） |

影片頁在 `< md` 時播放器全寬、控件下沉。

---

## 9. 落地優先級（對應 scaffold-redesign-plan P0-P3）

### Sprint 1 (P0) — 1 週

**前端**：
- [ ] 拆 `knowledge/page.tsx` → 抽 `useKnowledgePageState` hook
- [ ] 章節閱讀獨立路由 `/library/[stub]/reading`（含 generateStaticParams + window.location regex）
- [ ] 新元件 `RetrievalCard.tsx`、`InlinePractice.tsx`
- [ ] `useNodeScaffoldData(nodeId)` hook 統一 fetch

**設計**：
- [ ] 互動模式庫第 1 批（RetrievalCard / PitfallAlert / InlinePractice）Figma
- [ ] 章節閱讀頁 wireframe → high-fidelity

**教育**：
- [ ] 校稿 K-06-study prompt 的 retrieval_prompt 欄位產出規則
- [ ] 簽核章節練習選題策略（2-3 題 / 章節，按 source_page 對齊）

### Sprint 2 (P1) — 1 週

**前端**：
- [ ] 影片 viewer `/library/[stub]/watch`
- [ ] 考古題 viewer `/library/[stub]/quiz`
- [ ] `PitfallAlert.tsx` + `VideoTimestampJump.tsx`

**設計**：
- [ ] 影片頁 timestamped takeaway 視覺
- [ ] 考古題 viewer concept-extract layout

### Sprint 3 (P2) — 1.5 週

**前端**：
- [ ] PPT viewer `/library/[stub]/slides`
- [ ] 學習首頁重設計 `/`（取代 dashboard）
- [ ] 概念中心頁 `/library/{sid}/concept/[conceptId]` 骨架

### Sprint 4 (P3) — 1.5 週

**前端**：
- [ ] 跨資源連結 popover + 完整 concept-center 頁
- [ ] SM-2 排程整合至首頁「今日 3 件事」

---

## 10. 三方共識的「不做」清單

| 提議 | 否決方 | 理由 |
|------|--------|------|
| 圖譜當首頁 | 設計師 | 80% 用戶上來不是要探索，是要繼續學 |
| 一頁塞所有鷹架類型 | 教育顧問 + 前端 | 認知過載 + 前端 useState 失控 |
| 動畫處處飛 | 設計師 + 教育 | 干擾學習、強化認知負荷 |
| PPT 直接顯示 takeaway | 教育顧問 | fluency illusion |
| 考古題顯示 takeaway | 教育顧問 | 等於洩題 |
| 全平台同一 viewer | 前端 + 設計 + 教育 | 違反三方共識 |
| 自動播放影片 | 設計師 | A11y 災難 + 流量灼燒 |
| **影片強制每 3-5 分鐘暫停** | **CEO + 前端** | **過度工程、跨裝置不穩、用戶煩；改側欄時間戳 + 用戶自律** |

---

## 11. 開放決策題（送 CEO）

| # | 問題 | 選項 | 三方建議 |
|---|------|------|----------|
| Q1 | 是否把 `/dashboard` 改名 `/`（學習首頁）？ | 是 / 否 / 並存 | **是**（IA 重劃核心動作） |
| Q2 | 章節練習答錯題是否強制進複習清單？ | 強制 / 可選 | **強制**（學習科學要求） |
| Q3 | 圖譜（mindmap）降級為工具入口？ | 是 / 否 / 加 toggle | **是**（圖譜不是學習主動線） |
| Q4 | 影片頁是否強制每 3-5 分鐘暫停 retrieval？ | 強制 / 可關 / 不做 | ✅ **不做**（CEO 拍板）— 改側欄時間戳重點 + 用戶自律 |
| Q5 | 概念中心頁（P3）優先級是否拉前？ | P3 → P1 / 維持 | **維持 P3**（依賴 cross-resource embedding 成熟） |
| Q6 | 動效升級是否同步換新動效庫？ | Motion 12 升級 / 不動 | **不動**（穩定優先） |
| Q7 | 章節閱讀字體升級到 `text-base` | 升級 / 維持 sm | **升級**（A11y + 閱讀體驗） |

---

## 12. 風險矩陣

| 風險 | 機率 | 衝擊 | 緩解 |
|------|------|------|------|
| `knowledge/page.tsx` 拆分破壞既有功能 | 高 | 高 | 漸進式重構 + Snapshot 測試 + Chrome Preview 強制驗收 |
| 章節閱讀獨立路由被 Firebase rewrite 弄壞 | 中 | 高 | 雙版（有/無尾斜線）rewrite + BDD 測試 |
| 多檔案類型 viewer 設計工作量爆 | 高 | 中 | P0/P1 只做 PDF + Video，PPT/Audio 留 P2 |
| 教育顧問 / 設計師 / 前端意見衝突 | 中 | 中 | 每 Sprint Day 1 三方 30 分鐘對齊會議 |
| RWD 在 `< sm` 體驗變差（章節閱讀） | 中 | 中 | 行動版獨立 layout，不硬塞 |
| 跨資源連結品質差 (P3) | 高 | 中 | 預先用 voyage embedding 做 PoC |

---

## 13. 下一步

1. **CEO 簽核第 11 節決策題**（特別是 Q1 / Q3 IA 重大改動）
2. **設計師產出 Figma**：先做 RetrievalCard / PitfallAlert / InlinePractice + 章節閱讀頁 high-fidelity（**3 天**）
3. **教育顧問完成 K-06-study prompt schema 升級規格**（**2 天**）
4. **前端拆 PR：先做 P0 重構**（hook 抽離 + 章節獨立路由），不含新功能（**3-4 天**）
5. **CTO 排 Sprint 1 啟動**（建議 2026-05-15）

---

**附錄**：
- [Design.md](Design.md) — 既有視覺規範（色彩 / 字級 / 間距 token）
- [scaffold-redesign-plan.md](scaffold-redesign-plan.md) — 後端教學設計重構計畫
- 前端工程師獨立報告：本對話 2026-05-08 紀錄
