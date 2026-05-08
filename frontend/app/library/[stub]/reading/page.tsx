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
 *
 * Suspense 必須：client.tsx 內 useSearchParams() 在 static export 預渲染時
 * 必須被 Suspense 包住，否則 build 時噴 "missing-suspense-with-csr-bailout"。
 * Hotfix: 修 deploy 失敗（fix/p0-suspense-reading-route）。
 */
import { Suspense } from 'react';

import ReadingClient from './client';

export function generateStaticParams() {
  return [{ stub: 'read' }];
}

function ReadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<ReadingFallback />}>
      <ReadingClient />
    </Suspense>
  );
}
