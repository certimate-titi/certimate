/**
 * @file 路由 `/exam` — 區段錯誤邊界。
 *
 * 考試流程子樹（setup / workspace / results）的 segment-level error boundary。
 */
'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * 考試流程區段錯誤頁。
 */
export default function SegmentError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] px-4 text-center">
      <div className="h-16 w-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
        <AlertTriangle className="h-8 w-8 text-amber-500" />
      </div>
      <h2 className="text-2xl font-bold text-slate-900 mb-3">此頁面發生錯誤</h2>
      <p className="text-slate-600 max-w-md mx-auto mb-6 text-sm">
        這個區塊暫時無法載入，請重新整理或返回上一頁。
      </p>
      <div className="flex gap-3">
        <button
          onClick={() => reset()}
          className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          <RefreshCw className="h-4 w-4" /> 重試
        </button>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors"
        >
          回儀表板
        </Link>
      </div>
    </div>
  );
}
