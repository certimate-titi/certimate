/**
 * @file 路由 `/library/[stub]/concept` — 概念中心頁骨架（Sprint 4 T39）。
 *
 * UX 設計：
 * 顯示某個「概念」（如 No-code）在所有資源（PDF / 影片 / 考古題）的對照：
 * - PDF 教材怎麼講
 * - 影片講師怎麼示範（含時間戳）
 * - 考古題怎麼考（錯題率）
 * - 跨資源 pitfall 彙整
 *
 * Sprint 4 P3 範圍：純骨架 + 資料聚合邏輯（client-side 從 /parsed 撈 + 過濾）
 * Sprint 5 P4 評估：擴充後端 concept-center endpoint + voyage embedding 對齊
 */
import { Suspense } from 'react';

import ConceptClient from './client';

export function generateStaticParams() {
  return [{ stub: 'concept' }];
}

function ConceptFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function Page() {
  return (
    <Suspense fallback={<ConceptFallback />}>
      <ConceptClient />
    </Suspense>
  );
}
