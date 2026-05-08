/**
 * @file 路由 `/library/[stub]/slides` — PPT 簡報網格 / 全屏 viewer（Sprint 3 T27）。
 *
 * UX 設計：
 * - 縮圖網格 (4 列) → 點擊進全屏 viewer
 * - 全屏 viewer：左右翻頁 + 下方「請補完論述」slide_retrieval（type=takeaway）
 * - 連續 3 張看完彈 narrative_rebuild（type=elaborative）
 *
 * Sprint 3 簡化版：先做網格 + per-slide retrieval card，narrative_rebuild 留 P3
 */
import { Suspense } from 'react';

import SlidesClient from './client';

export function generateStaticParams() {
  return [{ stub: 'slides' }];
}

function SlidesFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<SlidesFallback />}>
      <SlidesClient />
    </Suspense>
  );
}
