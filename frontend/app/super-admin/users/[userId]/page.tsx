/**
 * @file 路由 `/super-admin/users/[userId]` — 使用者詳情頁（靜態匯出 stub）。
 *
 * 因 `output: 'export'` 限制，以 `generateStaticParams` 產出 `detail` stub；
 * 由 Firebase rewrite 將任意 userId 指向此 stub；UI 在 `client.tsx`。
 */
import UserDetailsPage from './client';

/** 靜態匯出 stub 參數，產出單一 detail 頁面檔。 */
export function generateStaticParams() {
  return [{ userId: 'detail' }];
}

/** 靜態匯出包裝：渲染 client.tsx 內的使用者詳情頁。 */
export default function Page() {
  return <UserDetailsPage />;
}
