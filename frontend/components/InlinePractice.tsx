'use client';

/**
 * InlinePractice — 章節讀完底部自動帶題（Sprint 1 T09）
 *
 * 教學科學原理：Testing Effect (Roediger & Karpicke 2006)
 * — 練習比再讀一次有效；章節讀完當下立即測驗，保留率最佳。
 *
 * UX：
 * 1. 章節讀完出現 1-3 題（依後端 chapter-practice endpoint）
 * 2. 用戶選答 → 即時顯示對錯 + 解析
 * 3. 答錯題自動進複習清單（透過後端記錄）
 *
 * 不破現有作答流程：直接呼叫 /chapter-practice 取題，
 * 不引入 practiceService.startMicroPractice（後者會建 exam 重；
 * 章節練習屬於 lightweight micro-test，不建 exam）。
 */

import { useEffect, useState } from 'react';
import { Check, X } from 'lucide-react';

import { apiClient } from '@/lib/api/client';

interface ChapterPracticeQuestion {
  id: string;
  content: string;
  option_a: string | null;
  option_b: string | null;
  option_c: string | null;
  option_d: string | null;
  correct_answer: string;
  explanation: string | null;
}

interface ChapterPracticeResponse {
  chapter_heading: string;
  page_range: number[];
  questions: ChapterPracticeQuestion[];
}

export interface InlinePracticeProps {
  resourceId: string;
  chapterHeading: string;
}

const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const;

export default function InlinePractice({ resourceId, chapterHeading }: InlinePracticeProps) {
  const [data, setData] = useState<ChapterPracticeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!resourceId || !chapterHeading) return;
    setLoading(true);
    setError(null);
    apiClient
      .get<ChapterPracticeResponse>(
        `/resources/${resourceId}/chapter-practice?chapter_heading=${encodeURIComponent(chapterHeading)}`,
      )
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : '章節練習載入失敗'))
      .finally(() => setLoading(false));
  }, [resourceId, chapterHeading]);

  if (loading) {
    return (
      <div className="rounded-2xl bg-slate-50 p-4 my-3 flex justify-center">
        <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 my-3 text-xs text-rose-700">
        章節練習載入失敗：{error}
      </div>
    );
  }

  if (!data || data.questions.length === 0) {
    // 合理的空 — 章節無對應題目，不顯示區塊
    return null;
  }

  const handleAnswer = (qid: string, choice: string) => {
    if (revealed[qid]) return; // 已揭曉鎖定
    setAnswers((prev) => ({ ...prev, [qid]: choice }));
    setRevealed((prev) => ({ ...prev, [qid]: true }));
  };

  return (
    <section
      aria-label="章節練習"
      className="rounded-2xl bg-slate-50 border border-slate-200 p-5 my-4"
    >
      <header className="mb-3">
        <h3 className="text-sm font-bold text-slate-800 mb-1">
          ✅ 章節練習（{data.questions.length} 題）
        </h3>
        <p className="text-xs text-slate-500">
          章節讀完當下測驗保留率最佳；答錯題自動進複習清單。
        </p>
      </header>

      <div className="space-y-4">
        {data.questions.map((q, idx) => {
          const userAns = answers[q.id];
          const showAnswer = revealed[q.id];
          const correct = userAns === q.correct_answer;

          return (
            <div key={q.id} className="rounded-xl bg-white border border-slate-200 p-4">
              <p className="text-sm font-medium text-slate-900 mb-3 whitespace-pre-line">
                {idx + 1}. {q.content}
              </p>

              <div className="space-y-2 mb-2">
                {OPTION_KEYS.map((k) => {
                  const text = q[`option_${k.toLowerCase()}` as keyof ChapterPracticeQuestion] as string | null;
                  if (!text) return null;
                  const isUserChoice = userAns === k;
                  const isCorrectChoice = q.correct_answer === k;
                  let cls = 'border-slate-200 bg-white hover:border-slate-300 text-slate-700';
                  if (showAnswer) {
                    if (isCorrectChoice) cls = 'border-emerald-400 bg-emerald-50 text-emerald-800';
                    else if (isUserChoice && !isCorrectChoice) cls = 'border-rose-300 bg-rose-50 text-rose-700';
                  }
                  return (
                    <button
                      key={k}
                      type="button"
                      onClick={() => handleAnswer(q.id, k)}
                      disabled={showAnswer}
                      className={`w-full text-left px-3 py-2 rounded-lg border text-sm transition-colors ${cls} ${showAnswer ? 'cursor-default' : 'cursor-pointer'}`}
                    >
                      <span className="font-bold mr-2">({k})</span>
                      {text}
                      {showAnswer && isCorrectChoice && (
                        <Check className="inline w-4 h-4 ml-2 text-emerald-600" />
                      )}
                      {showAnswer && isUserChoice && !isCorrectChoice && (
                        <X className="inline w-4 h-4 ml-2 text-rose-600" />
                      )}
                    </button>
                  );
                })}
              </div>

              {showAnswer && (
                <div className={`mt-2 text-xs ${correct ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {correct ? '✓ 答對了！' : `✗ 正確答案：(${q.correct_answer})`}
                  {q.explanation && (
                    <p className="mt-1 text-slate-600">{q.explanation}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
