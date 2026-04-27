# QA Charter — CertiMate 四層驗收

> 版本：v2（2026-04-27）— 因 `resource-library → /knowledge` 連結遺失 `subjectId` 漏網事件擴增 Layer 4
> 適用：所有 frontend / fullstack / 跨頁導航相關 PR

## 核心原則

QA 不是「跑通就好」。每次改動必須跑完四層，缺一退回。

| 層 | 名稱 | 一句話 |
|----|------|--------|
| 1 | 內容相關性 | 輸入 → 輸出對照表，內容語義必須對應 |
| 2 | 前端 UI 實測 | Chrome Preview 真實點擊，禁直接輸網址 |
| 3 | 空態區分 | 空畫面必查後端 job 表 + 前端 state，區分合理/錯位 |
| 4 | **跨頁導航契約**（新增） | Link/router.push 必驗目標頁完整狀態 |

---

## Layer 1 — 內容相關性（Content Relevance）

QA 報告必填對照表：

| 輸入 | 輸出 | 對應 | **導航前後一致性**（新增欄） |
|------|------|------|------------------------------|
| {上傳檔/查詢/點擊} | {DB 紀錄/UI 元素} | ✅/❌ | 來源頁參數 X = 目標頁狀態 X ✅ |

**新增欄位含意**：當輸出涉及跨頁（點連結 / router.push），必須在對照表中明確列出：
- 來源頁傳出的 query / state（例：`subjectId=A&resourceId=B`）
- 目標頁實際呈現的對應狀態（例：active subject = A，selected resource = B）
- 兩者一致 ✅；不一致 ❌（即使畫面看起來「有東西」也判退）

---

## Layer 2 — 前端 UI 實測（Chrome Preview）

### SOP（強制）

```
preview_start
↓
preview_fill / preview_click 登入
↓
導航到「來源頁」
↓
preview_snapshot（A）— 留證來源頁狀態
↓
preview_click 觸發跨頁連結（禁用 preview_eval / 直接輸網址）
↓
preview_snapshot（B）— 目標頁登陸態
↓
驗證以下三項：
  [a] URL query 完整保留（用 preview_eval 讀 location.search）
  [b] 目標頁 active state 與來源期待一致
  [c] 目標頁的關鍵 UI 元素正確 highlight / focus
↓
preview_console_logs --level error → 0 errors
↓
preview_screenshot 留證
```

### 違規範例

❌ 只 click 然後 screenshot 就簽核
❌ 用 `preview_eval` 模擬導航繞過 Link 與 Firebase rewrite
❌ 沒驗目標頁 active subject / focused entity 是否符合來源期待

---

## Layer 3 — 空態區分（Empty State Discrimination）

| 類型 | 判定條件 | 處理 |
|------|---------|------|
| 3a 合理的空 | DB 真無資料 + 用戶尚未操作 + 功能 opt-in | ✅ 簽核 |
| 3b 後端錯位空 | job 表 status=failed / RLS 過濾過度 / API 結構錯 | ❌ 退回查根因 |
| 3c 前端 state 錯位空 | active subject ≠ 目標 subject / param 解析失敗（stub 路由）/ state 條件分支失敗 | ❌ 退回查根因 |
| **3d 載入態誤判**（新增） | 資料還沒到就先渲染空態（缺 `*Loaded` flag / `loading` 守門） | ❌ 退回查根因 |

### 3d — 載入態誤判 SOP（強制）

對任何「條件渲染空態」的元件，QA 必跑：

1. **靜態 code 掃描**：搜尋 `.length === 0` / `!array.length` / 空態 early return，檢查同元件是否有對應 `*Loaded` flag 或 `loading` 守門。命中但無守門 → ❌ 退回。
2. **冷啟動三連測**：
   - 開無痕視窗 → 登入 → 直達該頁
   - 螢幕錄影前 3 秒；任何「載入中 → 空態 → 資料」閃爍 = ❌
3. **慢網路驗證**：必要時用 Chrome DevTools Network throttle 模擬 Slow 3G，確認 loading state 撐住、不會閃空態。

### 前端錯位空調查清單

```
1. URL 是否有正確 query？preview_eval `location.search`
2. useSearchParams 是否讀到？console.log 確認
3. localStorage active state 是否覆蓋了 query？讀 `localStorage.getItem(...)`
4. 動態路由是否走 Firebase rewrite stub？檢查 `useParams()` 是否回傳字面值
5. 條件渲染是否有過濾掉資料？看 documents.filter / .find 結果
```

---

## Layer 4 — 跨頁導航契約（NEW）

### 觸發條件

只要本次改動涉及以下任一，必跑 Layer 4：
- 新增/修改 `<Link href=...>` 或 `router.push(...)`
- 修改 query string / route param 解析
- 修改 useSearchParams / useParams 邏輯
- 修改 localStorage 與 URL 互動的狀態

### 強制檢查項

對每一個受影響的連結，QA 必須產出 **Link Contract 卡**：

```
## Link Contract: {來源頁路徑} → {目標頁路徑}

### 來源頁
- 元件：{file:line}
- 觸發物：<Link> / router.push / button onClick
- 傳出參數：
  - query: { subjectId, resourceId, ... }
  - state: { ... }（router.push state）

### 目標頁
- 元件：{file:line}
- 必讀參數：
  - useSearchParams: subjectId, resourceId
  - useParams: id
- 必呈現狀態：
  - active subject = subjectId
  - selected/focused entity = resourceId
  - 載入後該 entity 必須可見且高亮

### Chrome Preview 驗證紀錄
- [ ] 來源頁 snapshot
- [ ] click Link
- [ ] 目標頁 URL 完整保留
- [ ] 目標頁 active state 正確
- [ ] 目標頁焦點元素正確
- [ ] 0 console errors
```

### Link Contract 登記表

全站關鍵跨頁連結登記在 `docs/qa/link-contracts.md`。每次新增/修改連結時，PR 必須同步更新此檔。CTO Review 階段檢查連結是否登記。

---

## 退回判定

| 缺項 | 處理 |
|------|------|
| Layer 1 對照表缺少導航前後一致性 | ❌ 退回 |
| Layer 2 沒做目標頁 snapshot | ❌ 退回 |
| Layer 3 前端錯位空未調查 | ❌ 退回 |
| Layer 4 觸發但無 Link Contract 卡 | ❌ 退回 |
| Console 有 error（非已知豁免） | ❌ 退回 |

---

## 違規歷史

- **2026-04-13** 練習頁 API 欄位 `name` vs 型別 `label` — Layer 1 漏抓
- **2026-04-23** 學習鷹架空白實際是 parse job failed — Layer 3 漏抓（已加查 job 表）
- **2026-04-27** `/account/resource-library` → `/knowledge` 連結漏 `subjectId`，active subject 不符時退回首筆 — **Layer 4 漏抓**（本次新增此層的觸發點）
