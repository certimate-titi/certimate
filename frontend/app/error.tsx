/**
 * @file 應用程式 root error boundary。
 *
 * 當任何子路由未自行捕捉錯誤時，由此 root-level error boundary 接住，
 * 顯示通用錯誤訊息並提供「重試」與「返回首頁」按鈕。
 */
'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * 全站根錯誤頁。將錯誤輸出 console 並提供 reset 重試。
 */
export default function Error({
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
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <div className="h-20 w-20 bg-rose-100 rounded-full flex items-center justify-center mb-6">
        <AlertTriangle className="h-10 w-10 text-rose-500" />
      </div>
      <h2 className="text-3xl font-bold text-slate-900 mb-4">發生錯誤</h2>
      <p className="text-slate-600 max-w-md mx-auto mb-8">
        抱歉，系統發生了未預期的錯誤。我們已經記錄此問題並將盡快修復。
      </p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={() => reset()}
          className="inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-xl font-bold transition-colors shadow-md"
        >
          <RefreshCw className="h-4 w-4" /> 重新整理
        </button>
        <Link 
          href="/" 
          className="inline-flex items-center justify-center gap-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-6 py-3 rounded-xl font-bold transition-colors"
        >
          返回首頁
        </Link>
      </div>
    </div>
  );
}
