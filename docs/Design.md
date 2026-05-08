# CertiMate (TiTi) — 視覺規範 Design System

本文件為 CertiMate 前端視覺規範的 SSOT（單一事實來源）。所有頁面/元件 PR 須對齊本規範；新增 token 前先在此登記。

技術棧：Next.js 15 + TailwindCSS 4.1（無 `tailwind.config`，由 `@import "tailwindcss"` 啟用）+ Lucide Icons + Motion 12。
全部規範均基於目前線上程式碼的實際使用頻率（grep 統計）整理而成。

---

## 1. 設計理念

| 原則 | 說明 |
|------|------|
| **靜謐學習感** | Slate 中性色為主、emerald 為唯一強調色，避免高彩度造成備考焦慮 |
| **資訊密度低** | `text-sm` 為主要正文、配大量留白；表格與卡片優先 |
| **柔和邊角** | 卡片 `rounded-2xl` / 按鈕 `rounded-full`，避免硬直角 |
| **邀請式語氣** | 不用「已完成 / 必須」這類指令式文案；用「可試試 / 建議接下來」 |
| **動效節制** | 僅在狀態變化、慶祝節點（Confetti / Streak）使用 |

---

## 2. 色彩系統

### 2.1 品牌色

| Token | Hex | 用途 |
|-------|-----|------|
| `emerald-500` | `#10b981` | **主行動色**（CTA、Logo、Loading spinner、Active state） |
| `emerald-600` | `#059669` | 主行動 hover |
| `emerald-50` / `emerald-100` | — | 成功背景、卡片 hover 微底色 |
| `emerald-700` | — | 成功文字（高對比） |

### 2.2 中性色（Slate 系列為唯一中性色）

> **禁用** `gray-*` / `zinc-*` / `neutral-*` / `stone-*`，全站只用 `slate`。

| Token | 用途 |
|-------|------|
| `slate-900` | 主標題、強調文字 |
| `slate-800` / `slate-700` | 副標題、加強正文 |
| `slate-600` | 次要正文 |
| `slate-500` | **預設正文 / 說明文字** |
| `slate-400` | 占位符、不可選文字、icon 預設色 |
| `slate-300` | 邊界（罕用）、disabled 邊框 |
| `slate-200` | **預設邊框**（卡片、輸入框、分隔線） |
| `slate-100` | 內框、淺底分區 |
| `slate-50` | **頁面背景** |

### 2.3 狀態色

| 狀態 | 文字 | 背景 | 邊框 |
|------|------|------|------|
| **Success** | `emerald-700` | `emerald-50` / `emerald-100` | `emerald-500` |
| **Warning** | `amber-600` / `amber-700` | `amber-50` | `amber-200` |
| **Danger** | `rose-600` / `rose-700` | `rose-50` | `rose-200` |
| **Info** | `blue-600` | `blue-50` | `blue-200` |
| **Highlight** | `indigo-600` / `purple-600` | `indigo-50` / `purple-50` | — |

> 紅色一律用 `rose-*`，**不用** `red-*`，視覺上較溫和、減低備考挫敗感。

### 2.4 圖表 / Icon Hex

| Hex | 對應 |
|-----|------|
| `#10b981` | emerald-500 — 主數據 |
| `#64748b` | slate-500 — 次要數據 |
| `#e2e8f0` | slate-200 — 軸線 / 格線 |
| `#f59e0b` | amber-500 — 警示 |
| `#f43f5e` / `#ef4444` | rose-500 / red — 錯誤 / 退步 |
| `#6366f1` / `#8b5cf6` | indigo-500 / violet-500 — 進階指標 |

### 2.5 第三方品牌色

| 品牌 | Hex |
|------|-----|
| Google `#4285F4` / `#EA4335` / `#FBBC05` / `#34A853` |
| LINE `#06C755`（保留給未來整合） |

---

## 3. 字體與排版

### 3.1 字級（Type Scale）

| Token | px | 用途 | 出現頻率 |
|-------|------|------|----------|
| `text-xs` | 12 | 標籤、輔助說明、徽章 | ★★★★ |
| `text-sm` | 14 | **正文預設**、按鈕、表單 | ★★★★★ |
| `text-base` | 16 | 段落正文（資源詳情） | ★★ |
| `text-lg` | 18 | 卡片標題 | ★★ |
| `text-xl` | 20 | 區塊標題 | ★★ |
| `text-2xl` | 24 | 頁面 H2 | ★ |
| `text-3xl` | 30 | 頁面 H1（Dashboard 大數字） | ★ |
| `text-4xl` / `text-5xl` | 36 / 48 | 行銷頁、Hero、Onboarding 表情符號 | 罕用 |

### 3.2 字重

| Token | 用途 |
|-------|------|
| `font-bold` | 標題、強調數字 |
| `font-semibold` | 次標題、重要按鈕 |
| `font-medium` | 一般按鈕、選單項 |
| `font-normal` | 純說明文字（罕用，多數正文用 medium） |

### 3.3 字距與行高

- 行高：使用 Tailwind 預設 + 長段落加 `leading-relaxed`
- 中文標題避免 `tracking-tight`；長按鈕文字可用 `tracking-wide`

### 3.4 中文字型

不另指定，跟系統 `-apple-system, BlinkMacSystemFont, ...`。
**iOS 防 zoom**：`globals.css` 已設 `input/textarea/select { font-size: max(16px, 1rem); }`，新表單元件不要覆蓋。

---

## 4. 圓角（Radius）

| Token | 用途 |
|-------|------|
| `rounded-md` | 細小元素（罕用） |
| `rounded-lg` | 輸入框、小卡片、徽章 |
| `rounded-xl` | **預設卡片** |
| `rounded-2xl` | 大型卡片、Modal |
| `rounded-3xl` | Onboarding / Hero 卡片 |
| `rounded-full` | **按鈕（CTA pill）**、頭像、tag、圓點 |

> 圓形 CTA 按鈕是 TiTi 標誌風格之一，新按鈕請優先 `rounded-full`，除非與表單對齊（rounded-lg）。

---

## 5. 陰影

| Token | 用途 |
|-------|------|
| `shadow-sm` | **預設卡片** — 輕微浮起 |
| `shadow-md` | hover state |
| `shadow-lg` | Dropdown、Tooltip |
| `shadow-xl` / `shadow-2xl` | Modal、Onboarding 步驟卡 |

避免在頁面同時出現超過 2 種陰影層級。

---

## 6. 間距節奏（Spacing Rhythm）

主軸節奏：**4 / 8 / 12 / 16 / 24 px**（即 `1 / 2 / 3 / 4 / 6`）。

### 6.1 元件 padding

| 場景 | 建議 |
|------|------|
| 按鈕 | `px-3 py-2` 或 `px-4 py-2` |
| 卡片內 | `p-4` 預設、`p-5` 大型 |
| 列表項 | `px-3 py-2` 或 `px-4 py-3` |
| Modal | `p-6` 或 `p-8` |

### 6.2 排版 gap

| 場景 | 建議 |
|------|------|
| Icon + 文字 | `gap-1` 或 `gap-2` |
| 表單 row | `gap-3` 或 `space-y-3` |
| 卡片網格 | `gap-3` / `gap-4` |
| 區塊間 | `space-y-4` 或 `space-y-6` |

---

## 7. 容器寬度

| Token | 用途 |
|-------|------|
| `max-w-md` | 登入 / 表單卡 |
| `max-w-2xl` | 文章式內容 |
| `max-w-4xl` | 設定頁、Modal |
| `max-w-5xl` / `max-w-6xl` | **儀表板 / 主頁面預設** |
| `max-w-7xl` | 全寬列表（管理介面） |

預設頁面殼：`max-w-6xl mx-auto px-4 py-8`。

---

## 8. 元件規範

### 8.1 按鈕

```tsx
// Primary CTA
<button className="bg-emerald-500 hover:bg-emerald-600 text-white font-medium
                   px-4 py-2 rounded-full transition-colors">
  開始學習
</button>

// Secondary
<button className="bg-white border border-slate-200 hover:border-slate-300
                   text-slate-700 font-medium px-4 py-2 rounded-full">
  取消
</button>

// Danger
<button className="bg-rose-500 hover:bg-rose-600 text-white font-medium
                   px-4 py-2 rounded-full">
  刪除
</button>

// Ghost
<button className="text-slate-500 hover:text-slate-700 hover:bg-slate-100
                   px-3 py-2 rounded-lg">
  返回
</button>
```

### 8.2 卡片

```tsx
<div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5">
  <h3 className="text-lg font-bold text-slate-800 mb-2">{title}</h3>
  <p className="text-sm text-slate-500 leading-relaxed">{body}</p>
</div>
```

### 8.3 表單輸入

```tsx
<input
  className="w-full px-3 py-2 rounded-lg border border-slate-200
             focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100
             text-sm text-slate-800 placeholder:text-slate-400"
/>
```

### 8.4 徽章 / Tag

```tsx
<span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full
                 bg-emerald-50 text-emerald-700 text-xs font-medium">
  PRO
</span>
```

### 8.5 Loading Spinner

```tsx
<div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent
                rounded-full animate-spin" />
```

### 8.6 空態（Empty State）

```tsx
<div className="text-center py-12">
  <div className="text-5xl mb-4">📚</div>
  <h2 className="text-xl font-bold text-slate-800 mb-2">尚未上傳資源</h2>
  <p className="text-sm text-slate-500 mb-6 leading-relaxed">
    上傳 PDF / 圖片 / YouTube，TiTi 會幫你整理重點。
  </p>
  <button className="bg-emerald-500 hover:bg-emerald-600 text-white px-4 py-2 rounded-full">
    上傳第一份資源
  </button>
</div>
```

> 區分「合理空 vs 不合理空」見 `feedback_qa_empty_state_must_query_backend.md`：載入中必有 spinner、後端錯誤必有 retry。

---

## 9. 動效

| 場景 | 規範 |
|------|------|
| Hover / Active | `transition-colors`（顏色） / `transition-all`（多屬性） |
| 介入動畫 | Motion 12 — 預設 `ease-out`，duration `0.3s` 內 |
| 慶祝節點 | Confetti 粒子；連勝、達成成就時觸發 |
| Loading | `animate-spin`（spinner）/ `animate-pulse`（skeleton） |
| 禁忌 | 自動播放彈窗動畫、頁面進場大幅度位移、無限循環抓眼動畫 |

---

## 10. Icon

- **唯一來源**：`lucide-react`
- 預設大小：`w-4 h-4`（內聯）/ `w-5 h-5`（按鈕內）/ `w-6 h-6`（卡片角落）
- 預設顏色：跟父層 `text-*` color；獨立使用時 `text-slate-500`
- 不可使用 emoji 取代結構性 icon（行銷、空態、慶祝節點除外）

---

## 11. 響應式 Breakpoints

採用 Tailwind 預設：

| Token | min-width | 用途 |
|-------|-----------|------|
| `sm:` | 640 | 大型手機橫置 |
| `md:` | 768 | 平板 |
| `lg:` | 1024 | **預設桌機斷點** |
| `xl:` | 1280 | 大螢幕 |
| `2xl:` | 1536 | 罕用 |

行動優先：先寫 mobile 樣式，再加 `md:` / `lg:` 覆蓋。

`globals.css` 已設 `body { max-width: 100vw; overflow-x: clip; }`，新增 sticky 元素時請保留 clip（不要改回 hidden）。

---

## 12. 可用性（A11y）基本要求

- 觸控區 ≥ 44×44 px（Apple HIG）→ 按鈕至少 `py-2 px-3` + 字級 `text-sm`
- 文字對比度 ≥ 4.5:1：
  - 正文用 `text-slate-700` 以上於白底；`text-slate-500` 僅限說明
  - 在 `bg-emerald-500` 上必須白字
- Focus ring：表單輸入用 `focus:ring-2 focus:ring-emerald-100`
- 連結色與正文要可區分；現用 `text-emerald-600 hover:text-emerald-700 underline-offset-2 hover:underline`

---

## 13. 文案規範

| 禁用 | 改用 |
|------|------|
| 已整理好 / 已為你準備 / 準備完成 | 資源已匯入 / 建議接下來 / 可試試 |
| 必須完成 / 您要 / 請立即 | 完成後可⋯ / 試試 / 一起來 |
| 已通過 / 失敗 | 已完成 / 再試一次 |
| 純英文標籤（FREE / PRO） | 中英並列：「PRO 方案」 |

詳見 K-06 Prompt 內「禁用文案」段。

---

## 14. 命名與檔案位置

| 類型 | 位置 | 命名 |
|------|------|------|
| 通用元件 | `frontend/components/*.tsx` | PascalCase（如 `Navbar.tsx`） |
| 頁面 | `frontend/app/**/page.tsx` | 一律 `page.tsx`（Next.js App Router） |
| 客戶端拆分 | `client.tsx` | 同層附加 |
| 樣式 | 直接 Tailwind class，不寫 `.css` | 例外：`globals.css` |

---

## 15. 變更流程

1. 想新增 token / 元件 → 先在本文件登記 PR（CTO + 設計簽核）
2. 移除 token 前 → 跑 `grep -r "<token>" frontend/` 確認無使用
3. 任何違反「禁用 gray/red 文案」的 PR → CTO Review 退回
4. 視覺改動完工前必跑 `cd frontend && npx tsc --noEmit` + Chrome Preview 截圖留證

---

## 16. 待辦（已知缺口）

- [ ] 暗色模式（目前未支援，僅瀏覽器層 prefers-color-scheme）
- [ ] 設計 Token CSS variable 化（從 Tailwind class → `var(--color-primary)`），方便 B2B 機構自訂主題
- [ ] Storybook / 元件目錄自動生成
- [ ] 動效 timing token（duration/ease 統一）
