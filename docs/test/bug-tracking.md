# Bug Tracking — UI 驗收測試

**更新日期**: 2026-04-02

## 已修復

| ID | 嚴重度 | 頁面 | 描述 | 修復檔案 | 狀態 |
|----|--------|------|------|----------|------|
| BUG-001 | P0 | `/account` 訂閱Tab | `TypeError: Cannot read properties of undefined (reading 'documentsUploadedCount')` — 後端 API 回傳格式不匹配 | `frontend/app/account/page.tsx` L399-419 | ✅ 已修復 |
| BUG-002 | P1 | `/edu-console` | 學生列表永久 loading — API 回傳格式不含 students 陣列時缺乏空狀態處理 | `frontend/app/edu-console/page.tsx` 新增 isEmpty 狀態 + 空狀態 UI | ✅ 已修復 |

## 待修復

| ID | 嚴重度 | 頁面 | 描述 | 建議修復 | 狀態 |
|----|--------|------|------|----------|------|
| BUG-003 | P2 | `/feedback` | 品牌名稱顯示 "CertiMate" 而非 "TiTi" | 全域搜尋替換 | ❌ 待修復 |
| BUG-004 | P2 | `/exam/workspace` | Next.js 客戶端路由快取問題：進入 exam/workspace 後其他頁面導航全部被攔截 | 調查 Next.js prefetch cache 機制 | ❌ 待調查 |

## 前置條件問題（非 Bug）

| ID | 說明 | 解決方式 |
|----|------|----------|
| SETUP-001 | 新用戶註冊後 status=pending 無法登入 | `UPDATE users SET status='active' WHERE email='...'` |
| SETUP-002 | Onboarding 選科步驟顯示空白 | 需 seed `subject_categories` 和 `subjects` 資料 |
| SETUP-003 | Super Admin 帳號不存在 | 需手動 INSERT 到 users 表（role='super_admin'） |
