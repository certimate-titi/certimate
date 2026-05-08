'use client';

/**
 * RetrievalCard — 檢索觸發卡（Sprint 1 T08）
 *
 * 教學科學原理：Karpicke retrieval practice — 揭曉前必經一次主動回想，
 * 比直接看答案的保留率高 3 倍。
 *
 * UX 三階段：
 *   1. 摺疊（preview）：只顯示 retrieval_prompt 問句 + 「我想完了 看答案」按鈕
 *   2. 揭曉（revealed）：顯示 content + 自評回想感（沒想到/想到一半/完全想到）
 *   3. 自評後（rated）：顯示完整內容並感謝；可重置
 *
 * 後端互動：每次切階段 POST /resource-scaffolds/{id}/interactions
 * (event: viewed / revealed / recall_self_rated, recall_quality: none/partial/full)
 *
 * 視覺：摺疊用 amber 邊框（鼓勵思考）、揭曉後 emerald 邊框（已完成）。
 */

import { useEffect, useState } from 'react';
import { Lightbulb, Check } from 'lucide-react';

import { apiClient } from '@/lib/api/client';

export interface RetrievalCardProps {
  /** Scaffold UUID — 後端 interaction log 用 */
  scaffoldId: string;
  /** 章節標題（顯示用） */
  chapterHeading: string | null;
  /** Retrieval prompt 問句（摺疊狀態顯示） */
  retrievalPrompt: string;
  /** Takeaway 內容（揭曉後顯示） */
  content: string;
  /** 已揭曉狀態（從 localStorage 還原） */
  initialRevealed?: boolean;
  /** 揭曉後 callback（給 parent 紀錄） */
  onReveal?: () => void;
}

type RecallQuality = 'none' | 'partial' | 'full';

const RATING_LABELS: Record<RecallQuality, { label: string; emoji: string; color: string }> = {
  none: { label: '完全沒想到', emoji: '😅', color: 'bg-rose-50 hover:bg-rose-100 text-rose-700' },
  partial: { label: '想到一半', emoji: '🤔', color: 'bg-amber-50 hover:bg-amber-100 text-amber-700' },
  full: { label: '完全想到', emoji: '✨', color: 'bg-emerald-50 hover:bg-emerald-100 text-emerald-700' },
};

const STORAGE_KEY_PREFIX = 'certimate_retrieval_revealed_';

async function logInteraction(
  scaffoldId: string,
  event: 'viewed' | 'revealed' | 'recall_self_rated',
  recallQuality?: RecallQuality,
): Promise<void> {
  try {
    await apiClient.post(`/resource-scaffolds/${scaffoldId}/interactions`, {
      event,
      recall_quality: recallQuality ?? null,
    });
  } catch (e) {
    console.warn('[RetrievalCard] log interaction failed (non-fatal)', e);
  }
}

export default function RetrievalCard({
  scaffoldId,
  chapterHeading,
  retrievalPrompt,
  content,
  initialRevealed = false,
  onReveal,
}: RetrievalCardProps) {
  const storageKey = `${STORAGE_KEY_PREFIX}${scaffoldId}`;
  const [revealed, setRevealed] = useState<boolean>(() => {
    if (initialRevealed) return true;
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(storageKey) === '1';
  });
  const [rating, setRating] = useState<RecallQuality | null>(null);
  const [viewLogged, setViewLogged] = useState(false);

  // Log "viewed" once per scaffold mount (initial exposure)
  useEffect(() => {
    if (viewLogged) return;
    void logInteraction(scaffoldId, 'viewed');
    setViewLogged(true);
  }, [scaffoldId, viewLogged]);

  const handleReveal = () => {
    setRevealed(true);
    if (typeof window !== 'undefined') localStorage.setItem(storageKey, '1');
    void logInteraction(scaffoldId, 'revealed');
    onReveal?.();
  };

  const handleRate = (q: RecallQuality) => {
    setRating(q);
    void logInteraction(scaffoldId, 'recall_self_rated', q);
  };

  if (!revealed) {
    return (
      <section
        aria-label="檢索觸發卡 — 想想看"
        className="rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50/50 p-4 my-3"
      >
        <header className="flex items-center gap-2 mb-2">
          <Lightbulb className="w-4 h-4 text-amber-600" />
          <span className="text-xs font-bold text-amber-700">想想看</span>
          {chapterHeading && (
            <span className="text-xs text-amber-600/70">{chapterHeading}</span>
          )}
        </header>
        <p className="text-base font-medium text-slate-900 leading-relaxed mb-3">
          {retrievalPrompt}
        </p>
        <p className="text-xs text-amber-600 mb-3">
          ⏱ 先給自己 30 秒回想，再看答案 — 主動回想比直接看記得久。
        </p>
        <button
          type="button"
          onClick={handleReveal}
          className="px-4 py-2 rounded-full bg-amber-500 text-white text-sm font-medium hover:bg-amber-600 transition-colors"
        >
          我想完了，看答案 →
        </button>
      </section>
    );
  }

  return (
    <section
      aria-label="已揭曉重點"
      className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-4 my-3"
    >
      <header className="flex items-center gap-2 mb-2">
        <Check className="w-4 h-4 text-emerald-600" />
        <span className="text-xs font-bold text-emerald-700">已揭曉</span>
        {chapterHeading && (
          <span className="text-xs text-emerald-600/70">{chapterHeading}</span>
        )}
      </header>
      <p className="text-sm text-slate-500 italic mb-2">{retrievalPrompt}</p>
      <p className="text-base text-slate-800 leading-relaxed mb-4">{content}</p>

      {!rating ? (
        <div>
          <p className="text-xs text-slate-600 mb-2">你的回想感覺：</p>
          <div className="flex flex-wrap gap-2">
            {(Object.keys(RATING_LABELS) as RecallQuality[]).map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => handleRate(q)}
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${RATING_LABELS[q].color}`}
              >
                {RATING_LABELS[q].emoji} {RATING_LABELS[q].label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-xs text-emerald-700">
          ✓ 已紀錄「{RATING_LABELS[rating].label}」— 影響後續複習排程。
        </p>
      )}
    </section>
  );
}
