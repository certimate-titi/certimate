/**
 * @file 路由 `/library/[stub]/reading` — 章節閱讀頁（靜態匯出 stub）。
 *
 * Sprint 1 T07：把章節閱讀從 /knowledge?docId= 拆出來成獨立 URL，
 * 可直接書籤 / 分享 / 瀏覽器返回鍵正確。
 *
 * 因 `output: 'export'` 不支援動態路由 SSR，以 `generateStaticParams`
 * 產出單一 `read` stub；真正參數從 query string 取（?docId=&subjectId=&chapter=）。
 *
 * Firebase rewrite 須對有/無尾斜線兩版都映射到
 * /library/read/reading/index.html（雙版避免 404）。
 */
import ReadingClient from './client';

export function generateStaticParams() {
  return [{ stub: 'read' }];
}

export default function Page() {
  return <ReadingClient />;
}
