'use client';

/**
 * PitfallAlert — 迷思警示卡（Sprint 2 P1 T15）
 *
 * 教學科學原理：Misconception Correction
 * — 顯式對比「常見誤解 vs 正確理解」，避免錯誤心智模型固化。
 *
 * UX：
 * - 紅色 rose-200 邊框、rose-50 底色 + ⚠️ icon
 * - 預設展開（不像 RetrievalCard 摺疊）：警示性內容應第一時間被看到
 * - 可選「我懂了，不再提醒」按鈕（dismiss only this scaffold for current user）
 *   → 寫入 localStorage（per-scaffoldId），不打 API（lightweight）
 *
 * 與 RetrievalCard 區別：
 *   - RetrievalCard 摺疊揭曉式（檢索練習）
 *   - PitfallAlert 直接顯示（警示型）
 */

import { useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';
import MathContent from '@/components/MathContent';

export interface PitfallAlertProps {
  /** Scaffold UUID — 用於 localStorage dismiss key */
  scaffoldId: string;
  /** 章節標題（顯示用） */
  chapterHeading: string | null;
  /** Pitfall 內容（含「⚠️ 很多人以為⋯ 其實⋯」對比結構） */
  content: string;
}

const STORAGE_KEY_PREFIX = 'certimate_pitfall_dismissed_';

export default function PitfallAlert({
  scaffoldId,
  chapterHeading,
  content,
}: PitfallAlertProps) {
  const storageKey = `${STORAGE_KEY_PREFIX}${scaffoldId}`;
  const [dismissed, setDismissed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(storageKey) === '1';
  });

  if (dismissed) return null;

  const handleDismiss = () => {
    setDismissed(true);
    if (typeof window !== 'undefined') localStorage.setItem(storageKey, '1');
  };

  return (
    <section
      aria-label="迷思警示卡"
      className="rounded-2xl border border-rose-200 bg-rose-50 p-4 my-3 relative"
    >
      <button
        type="button"
        onClick={handleDismiss}
        className="absolute top-2 right-2 p-1 rounded-full hover:bg-rose-100 text-rose-400 hover:text-rose-700 transition-colors"
        aria-label="關閉警示"
        title="我懂了，不再提醒"
      >
        <X className="w-3.5 h-3.5" />
      </button>
      <header className="flex items-center gap-2 mb-2 pr-6">
        <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
        <span className="text-xs font-bold text-rose-700">常見迷思</span>
        {chapterHeading && (
          <span className="text-xs text-rose-600/70">{chapterHeading}</span>
        )}
      </header>
      <div className="text-sm text-slate-800 leading-relaxed">
        <MathContent>{content}</MathContent>
      </div>
    </section>
  );
}
