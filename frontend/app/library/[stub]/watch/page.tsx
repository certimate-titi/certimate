/**
 * @file 路由 `/library/[stub]/watch` — 影片觀看頁（Sprint 2.5 T21）。
 *
 * UX 設計依 ux-redesign-plan.md：
 * - 上方影片播放器（HTML5 video 或 YouTube embed）
 * - 右側時間戳重點清單（takeaway / pitfall）
 * - 點 takeaway 跳到對應秒數（VideoTimestampJump）
 * - 不強制暫停（per CEO Q4 決議）
 *
 * 靜態匯出 stub 模式同 reading 頁，stub='view'。
 * Suspense 必須包（避免 useSearchParams prerender 失敗）。
 */
import { Suspense } from 'react';

import WatchClient from './client';

export function generateStaticParams() {
  return [{ stub: 'view' }];
}

function WatchFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<WatchFallback />}>
      <WatchClient />
    </Suspense>
  );
}
