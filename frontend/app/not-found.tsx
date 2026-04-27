/**
 * @file 全站 404 頁。
 *
 * Next.js 內建慣例：當 URL 找不到對應路由時自動渲染此元件。
 */
import Link from 'next/link';
import { AlertCircle, ArrowRight } from 'lucide-react';

/**
 * 全站 404 找不到頁面。提供返回首頁的連結。
 */
export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4 text-center">
      <div className="h-20 w-20 bg-slate-100 rounded-full flex items-center justify-center mb-6">
        <AlertCircle className="h-10 w-10 text-slate-400" />
      </div>
      <h2 className="text-3xl font-bold text-slate-900 mb-4">找不到頁面</h2>
      <p className="text-slate-600 max-w-md mx-auto mb-8">
        抱歉，您尋找的頁面不存在或已被移除。請確認網址是否正確，或返回首頁。
      </p>
      <Link 
        href="/" 
        className="inline-flex items-center justify-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold transition-colors shadow-md"
      >
        返回首頁 <ArrowRight className="h-4 w-4" />
      </Link>
    </div>
  );
}
