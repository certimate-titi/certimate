/**
 * @file 路由 `/library/[stub]/quiz` — 考古題試題卷答題頁（Sprint 2.5 T23）。
 *
 * UX：一題一頁全屏作答，答完才顯示 concept_extract（避免洩答）。
 *
 * 對應 K-06-quiz prompt 模板：
 * - 不寫 takeaway / strategy
 * - 寫 concept_extract（解題後對照）+ pitfall（常見錯選陷阱）
 * - variation 寫入 questions 表（不在此頁）
 */
import { Suspense } from 'react';

import QuizClient from './client';

export function generateStaticParams() {
  return [{ stub: 'quiz' }];
}

function QuizFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<QuizFallback />}>
      <QuizClient />
    </Suspense>
  );
}
