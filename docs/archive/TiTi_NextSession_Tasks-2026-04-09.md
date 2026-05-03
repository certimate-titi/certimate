# 下一個 Session 待辦

**日期**：2026-04-09
**上下文**：V3 有機生長動態圖譜已完成核心架構，前端三欄拖曳佈局已修正。

---

## 🔴 最高優先：knowledge/page.tsx JSX 結構修復

右側面板（line 322-513）有 6 個未關閉的 `<div>`。
原因：多次增量編輯導致 JSX 層級混亂。
修復方式：**從 line 322 開始完整重寫右側面板 JSX**（不要增量修改）。

結構應為：
```jsx
{showRightPanel && (
  <div className="w-[320px] shrink-0 border-l border-slate-200">
    <div className="h-full flex flex-col bg-white">
      {/* 上：節點說明 */}
      <div className="max-h-[50%] shrink-0 border-b overflow-y-auto">
        {loadingDetail ? (...) : selectedNodeDetail ? (...) : (...)}
      </div>
      {/* 下：AI 教練 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        ...header + messages + input...
      </div>
    </div>
  </div>
)}
```

## 待修復

### 1. 三欄拖曳驗證
- `react-resizable-panels` v4.9 使用 `Group`/`Panel`/`Separator` API
- 需要在瀏覽器實際測試拖曳是否流暢
- Separator 的 hover 樣式（`bg-emerald-400`）是否可見

### 2. 知識點弱點分析無內容
- `/knowledge` 頁面點選節點後，右側「節點說明」可能為空
- 原因：`selectedNodeDetail.citationText` 和 `sourceText` 可能為 null
- 修復：如果 API 回傳空內容，顯示 fallback（節點名稱 + 可用題數 + 生成測驗按鈕）

### 3. 測驗結果頁面加入心智圖
- 位置：`/exam/results` 頁面
- 需求：顯示 ForceGraph，標示本次考試影響的節點進度變化
- 實作：
  1. 讀取 `frontend/app/exam/results/page.tsx`
  2. 呼叫 knowledge-map API 取得節點
  3. 加入 `<ForceGraph>` 元件
  4. Highlight 進度有變化的節點（用不同顏色/動畫）

### 4. 考試內容與考科考古題對不起來
- 董事會提到考試生成的題目與考科的考古題不匹配
- 可能原因：
  - `exam_service.py` 的 `submit_config` 推導 subject_id 邏輯有誤
  - 考古題匯入時的 `historical_exam.exam_code` 與前端的 `subject_id` 不對應
  - 需要檢查 exam config → knowledge node → historical exam 的關聯鏈

---

## 已完成（本次 session）

1. ✅ V3 有機生長引擎（organic_progress.py）
2. ✅ Practice 即時寫入 DB（權重 0.5）
3. ✅ Celery Fan-out 批次重算
4. ✅ ForceGraph 力導向圖（D3.js）
5. ✅ 三欄可拖曳佈局（react-resizable-panels）
6. ✅ 節點說明移到右側上方
7. ✅ AI 教練在右側下方
8. ✅ 淺色背景 + TiTi 品牌色
9. ✅ Migration 043（version 樂觀鎖）
10. ✅ BDD Feature 04: 25/25 通過
11. ✅ 前端 build: 32 頁面匯出成功
