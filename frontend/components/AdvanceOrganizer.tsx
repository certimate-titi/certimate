'use client';

/**
 * AdvanceOrganizer — 讀前定錨卡（Sprint 4 P3 T35）
 *
 * 教學科學原理：Ausubel Subsumption Theory
 * — 閱讀章節**前**先看的引導問句，幫讀者先建立心智錨點，
 *   比讀後總結對保留率影響更大。
 *
 * UX：
 * - 顯示在章節閱讀面板**上方**（與章節結尾 takeaway/pitfall 區分位置）
 * - 預設展開（鼓勵讀者先思考），但可摺疊
 * - 紫色 violet-50 配色（區別 takeaway emerald / pitfall rose）
 * - 含「我已思考過，繼續閱讀 ↓」按鈕（dismiss + scroll）
 *
 * 與其他鷹架元件區別：
 * - RetrievalCard（amber → emerald）：讀後檢索觸發
 * - PitfallAlert（rose）：警示型，預設展開
 * - AdvanceOrganizer（violet）：讀前定錨，預設展開
 */

import { useState } from 'react';
import { Lightbulb, ArrowDown, ChevronUp } from 'lucide-react';
import MathContent from '@/components/MathContent';

export interface AdvanceOrganizerProps {
  scaffoldId: string;
  chapterHeading: string | null;
  content: string;
  onContinue?: () => void;
}

const STORAGE_KEY_PREFIX = 'certimate_organizer_acked_';

export default function AdvanceOrganizer({
  scaffoldId,
  chapterHeading,
  content,
  onContinue,
}: AdvanceOrganizerProps) {
  const storageKey = `${STORAGE_KEY_PREFIX}${scaffoldId}`;
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(storageKey) === '1';
  });

  const handleAck = () => {
    setCollapsed(true);
    if (typeof window !== 'undefined') localStorage.setItem(storageKey, '1');
    onContinue?.();
  };

  if (collapsed) {
    return (
      <button
        type="button"
        onClick={() => setCollapsed(false)}
        className="w-full text-left rounded-xl border border-violet-200 bg-violet-50/40 p-2 my-2 text-xs text-violet-700 hover:bg-violet-50 flex items-center gap-2"
        aria-label="重新展開讀前定錨"
      >
        <ChevronUp className="w-3.5 h-3.5" />
        讀前定錨已收合（點擊重新展開）
      </button>
    );
  }

  return (
    <section
      aria-label="讀前定錨卡"
      className="rounded-2xl border border-violet-200 bg-violet-50/60 p-4 my-3"
    >
      <header className="flex items-center gap-2 mb-2">
        <Lightbulb className="w-4 h-4 text-violet-600 shrink-0" />
        <span className="text-xs font-bold text-violet-700">讀前定錨</span>
        {chapterHeading && (
          <span className="text-xs text-violet-600/70">{chapterHeading}</span>
        )}
      </header>
      <div className="text-base text-slate-800 leading-relaxed mb-3">
        <MathContent>{content}</MathContent>
      </div>
      <p className="text-xs text-violet-600 mb-3">
        💡 帶著這個問題讀章節，效果比直接讀好得多（Ausubel 1968）
      </p>
      <button
        type="button"
        onClick={handleAck}
        className="px-4 py-2 rounded-full bg-violet-500 text-white text-sm font-medium hover:bg-violet-600 transition-colors flex items-center gap-1"
      >
        我已思考過，繼續閱讀 <ArrowDown className="w-3.5 h-3.5" />
      </button>
    </section>
  );
}
