/**
 * @file 路由 `/resources/[id]/candidates` — 題目候選審核頁（靜態匯出 stub）。
 *
 * 因 `output: 'export'` 不支援動態路由 SSR，以 `generateStaticParams`
 * 產出單一 `detail` stub 檔，由 Firebase rewrite 將所有 UUID 指向此 stub；
 * 真正的 UI 在 `client.tsx` 中以 pathname regex 解析 resource id。
 */
import CandidatesClient from './client';

/** 靜態匯出 stub 參數，產出單一 detail 頁面檔。 */
export function generateStaticParams() {
  return [{ id: 'detail' }];
}

/** 靜態匯出包裝：渲染 client.tsx 內的候選題目審核頁。 */
export default function Page() {
  return <CandidatesClient />;
}
