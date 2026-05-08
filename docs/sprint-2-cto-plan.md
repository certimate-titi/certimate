# Sprint 2 CTO 開發計畫書

**Sprint 期程**：2026-05-09 → 2026-05-15（7 天）
**對應**：[scaffold-redesign-plan.md](scaffold-redesign-plan.md) P1 + [ux-redesign-plan.md](ux-redesign-plan.md) Sprint 2
**Worktree**：本地 worktree 直接 commit；通過 QA 後批量 push
**進度追蹤**：每日更新本文件 + TodoWrite

---

## 0. Sprint 2 範圍

### 必交付（P1 優先級）

1. **pitfall 鷹架類別**（E3 教育顧問要求）
   - 跨類型通用，從錯題分布反推迷思警示
2. **K-06-quiz prompt 模板**（試題卷分流）
   - 不寫 takeaway（避免洩答）→ 改寫 concept_extract + variation
3. **K-06-video prompt 模板**（影片時間戳）
   - takeaway 必含 start_time_sec / end_time_sec
4. **Prompt routing logic**
   - 按 file_type / detected_content_type 自動分流選對 prompt
5. **PitfallAlert 元件** — 跨類型通用 UI
6. **影片 viewer** `/library/[stub]/watch` — HTML5 video + 時間戳側欄
7. **考古題 viewer** `/library/[stub]/quiz` — 答完才顯示 concept_extract

### 不做（順延 Sprint 3+）

- K-06-slides / K-06-audio / K-06-notes / K-06-image 模板
- 跨資源連結（concept-center 頁）
- E4 advance_organizer 讀前定錨
- E5 interleaving 跨章節提示
- E6 SM-2 排程演算法整合
- IA 重劃（dashboard → /、knowledge → /library）
- ESLint setState-in-effect 重構（Sprint 1 P0 遺留）

---

## 1. 任務拆解（10 個 commit / 1 PR 整合）

| # | 任務 | 預估 | 優先 | 依賴 |
|---|------|------|------|------|
| **T11** | Migration 083：ResourceScaffoldType add `pitfall` enum value | 1 hr | P1a | 無 |
| **T12** | ORM `ResourceScaffoldType.PITFALL` value | 0.5 hr | P1a | T11 |
| **T13** | K-06 prompt v5 加 pitfall 產出規則（含教育顧問規格）| 2 hr | P1b | 無（並行）|
| **T14** | Backend `_persist_parsed` 接受 pitfall + 防重複 | 1.5 hr | P1c | T11+T13 |
| **T15** | `PitfallAlert.tsx` 元件 + reading client 整合 | 4 hr | P1d | T14 |
| **T16** | K-06-quiz prompt 模板（concept_extract / variation）| 3 hr | P1e | 無（並行）|
| **T17** | K-06-video prompt 模板（timestamped takeaway）| 3 hr | P1f | 無（並行）|
| **T18** | Prompt routing：按 file_type / detected_content_type 分流 | 4 hr | P1g | T13+T16+T17 |
| **T19** | BDD scenarios（feature 38 pitfall + feature 39 quiz/video）+ QA Layer 1-3 | 5 hr | P1h | 全部完成 |
| **T20** | PR open + CTO review + 雲端 deploy + 雲端 QA Layer 4 + 教育顧問會稿 | 4 hr | P1i | T19 |

**總工時估算**：28 hr（單人 4 工作天，預留 3 天 buffer + QA + PR review）

---

## 2. 依賴圖

```
T11 (migration 083) ──→ T12 (ORM enum) ──┐
                                          ├──→ T14 (backend) ──→ T15 (PitfallAlert)
T13 (K-06 v5 pitfall rules) ─────────────┘
                                                                  ↓
T16 (K-06-quiz)  ──┐                                              │
T17 (K-06-video) ──┼──→ T18 (routing logic) ──────────────────────┤
                                                                  ↓
                                                              T19 (BDD + QA)
                                                                  ↓
                                                              T20 (PR + cloud QA)
```

**並行機會**：
- Day 1：T11 + T13 + T16 + T17 並行（互不依賴）
- Day 2：T12 + T14 + T18 並行（依賴成熟）
- Day 3：T15 整合（依賴 T14）+ 影片 viewer / 考古題 viewer（沿用 P0 reading 模式）
- Day 4：T19 BDD + QA
- Day 5：T20 PR + 雲端 QA

---

## 3. 進度追蹤表

| ID | 任務 | 狀態 | 開始 | 完成 | 備註 |
|----|------|------|------|------|------|
| Plan | Sprint 2 計畫書 | 🔄 | 2026-05-09 | — | — |
| T11 | Migration 083 pitfall enum | ⏳ | — | — | — |
| T12 | ORM enum value | ⏳ | — | — | — |
| T13 | K-06 v5 pitfall rules | ⏳ | — | — | — |
| T14 | _persist_parsed pitfall + dedup | ⏳ | — | — | — |
| T15 | PitfallAlert 元件 | ⏳ | — | — | — |
| T16 | K-06-quiz prompt | ⏳ | — | — | — |
| T17 | K-06-video prompt | ⏳ | — | — | — |
| T18 | Prompt routing logic | ⏳ | — | — | — |
| T19 | BDD + QA | ⏳ | — | — | — |
| T20 | PR + cloud QA + 教育會稿 | ⏳ | — | — | — |

---

## 4. 關鍵技術決定

### 4.1 pitfall 鷹架特性
- 教學原理：Misconception Correction
- 來源：兩種抽法
  - **資源內**：K-06 直接從教材文本反向找出常見誤解（per chapter 0-1 條）
  - **跨資源**：從考古題錯題分布反推（需要 ≥50 題才有統計意義，P1 暫不做，留 P3）
- 與 takeaway 區別：takeaway 是「要記住的」，pitfall 是「容易誤解的」
- UI：紅色 rose-50/rose-200 警示卡片，預設展開（不需 retrieval-first）

### 4.2 K-06-quiz 不寫 takeaway
- 教育顧問否決：考古題寫 takeaway 等於先洩答
- 改寫 `concept_extract`：「這題核心概念」（解題後對照用）
- variation：「同概念換題幹」寫入 question_candidates 標 generated_from

### 4.3 K-06-video timestamped output
- 新欄位 `start_time_sec / end_time_sec` 加在 takeaway 與 pitfall
- 前端 VideoTimestampJump 點 takeaway 跳到對應秒數
- 影片不強制暫停（per CEO Q4 決議）

### 4.4 Routing logic
```python
def _select_prompt(resource: Resource) -> str:
    ext = (resource.gcs_path or "").lower().rsplit(".", 1)[-1]
    if ext in ("mp4", "mov", "avi", "mkv", "webm"): return "K-06-video"
    if resource.youtube_url: return "K-06-video"
    if resource.detected_content_type == "practice_questions": return "K-06-quiz"
    return "K-06-study"  # default
```
- detected_content_type 由 K-01 Flash 預判（已存在）
- ext 非 ASCII / 未知 → fallback K-06-study

### 4.5 schema migration 083
- ResourceScaffoldType enum add `pitfall`
- Postgres ALTER TYPE ... ADD VALUE（同一 transaction 不能同時新增 + 使用，須兩階段）
- 不影響歷史資料

### 4.6 不重新解析歷史資源（per CEO Q1 決議：lazy backfill）
- pitfall 只在新上傳資源出現
- 用戶手動觸發 reparse（若未來開放此功能）才會補

---

## 5. 預期困難與風險

| 風險 | 影響 | 緩解 |
|------|------|------|
| Postgres ALTER TYPE 不能在同 tx 新增 + 使用 enum value | 中 | migration 拆兩階段 commit / 用 `op.execute('ALTER TYPE ...')` |
| K-06-video 多次 LLM 呼叫成本爆 | 中 | 限定影片 ≤ 30 分鐘；超過走分段（類似 D 智慧分流）|
| 考古題答案外洩風險 | 高 | K-06-quiz prompt 強制不產 takeaway；BDD 必驗 detected=practice_questions 時 takeaway=[] |
| Routing 誤判（mixed PDF）| 中 | UI 加「使用者覆寫分類」按鈕（移到 Sprint 3）；目前 K-06-study 作 fallback |
| 影片 viewer cross-browser 一致性 | 中 | 用 HTML5 `<video controls>`，不另寫播放器 |
| Pre-existing ESLint setState 警告 | 低 | 暫不重構，不影響 build |

---

## 6. 退出條件（Sprint 2 完成判定）

- ✅ 10 個 T11-T20 任務 commit 完成 + 整合 PR merge
- ✅ Frontend `tsc --noEmit` 0 錯誤
- ✅ Backend `behave --tags=~@ignore` 全綠
- ✅ Pre-Board Gate 15 項自檢全綠
- ✅ Cloud deploy 成功（無 Suspense 等預渲染陷阱）
- ✅ 雲端 QA 三層複測通過
- ✅ 教育顧問抽樣 pitfall / quiz concept_extract / video timestamped takeaway 真實 LLM 產出 ≥ 4 星
- ✅ Sprint 2 cloud QA report 歸檔

---

## 7. CTO 心跳模板

```
## Sprint 2 Day {N} 心跳 - {date}

完成：T1X (commit hash)
進行中：T1Y ({progress}%)
阻塞：{若無寫無)
明日：T1Z
風險：{若無寫無)
```

---

## 8. 下一步

開始 T11 — Migration 083 ResourceScaffoldType add pitfall enum value.
