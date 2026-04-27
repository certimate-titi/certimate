/**
 * @file 路由 `/edu-console/student/[id]` — 學生詳情頁（靜態匯出 stub）。
 *
 * 因為前端為 `output: 'export'`，動態路由必須以 `generateStaticParams`
 * 產出單一 stub 檔，再由 Firebase rewrite 將所有 UUID 指向此 stub；
 * 真正的 UI 在 `client.tsx` 內以 `window.location.pathname` 解析 ID。
 */
import StudentDetailPage from './client';

/** 靜態匯出 stub 參數，產出單一 detail 頁面檔。 */
export function generateStaticParams() {
  return [{ id: 'detail' }];
}

/** 靜態匯出包裝：渲染 client.tsx 內的學生詳情頁。 */
export default function Page() {
  return <StudentDetailPage />;
}
