'use client';

/**
 * 考古題試題卷答題頁 — Sprint 2.5 T23
 *
 * 路徑：/library/quiz/quiz?docId={uuid}&subjectId={uuid}
 *
 * UX 流程：
 * 1. 載入該資源所有 question_candidates（已 approved 的轉成 questions 仍可走此頁）
 * 2. 一題一張卡片，4 選項按鈕作答
 * 3. 答完顯示「答對 / 答錯 + 正確答案」
 * 4. 同時揭曉該題對應的 concept_extract（K-06-quiz scaffold 中的 type=takeaway 但
 *    template_code='K-06-quiz' 區分）+ pitfall（若有）
 *
 * 與 InlinePractice 區別：
 * - InlinePractice 是章節讀完底部「微練習」（章節級題）
 * - QuizClient 是「整份考古題試題卷」全卷答題模式
 */

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, Check, X, AlertTriangle } from 'lucide-react';

import PitfallAlert from '@/components/PitfallAlert';
import MathContent from '@/components/MathContent';
import { resourceParseService } from '@/lib/api/services';
import { useAuth } from '@/lib/auth-context';
import type { ScaffoldEntry } from '@/hooks/use-reading-page-state';

interface QuizQuestion {
  id: string;
  content: string;
  option_a: string | null;
  option_b: string | null;
  option_c: string | null;
  option_d: string | null;
  correct_answer: string;
  explanation: string | null;
}

const OPTION_KEYS = ['A', 'B', 'C', 'D'] as const;

export default function QuizClient() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const resourceId = searchParams.get('docId') ?? '';
  const subjectId = searchParams.get('subjectId') ?? '';

  const [scaffolds, setScaffolds] = useState<ScaffoldEntry[]>([]);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [filename, setFilename] = useState<string>('');
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!resourceId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all([
      resourceParseService.getMarkdown(resourceId).catch(() => null),
      resourceParseService.getParsed(resourceId).catch(() => null),
      // 直接抓全 resource 的 chapter-practice（empty heading）— 沒有的話 fallback 用 question_candidates
      // P1 簡化：只用 /parsed 的 scaffolds + 從 chapter heading "Q1 ..." 推題
    ]).then(([md, parsed]) => {
      if (cancelled) return;
      const meta = md as { filename?: string };
      setFilename(meta?.filename ?? '考古題');
      const sc = (parsed as unknown as { scaffolds?: ScaffoldEntry[] })?.scaffolds ?? [];
      setScaffolds(sc);
      // 簡化版：從 scaffolds 中 extract question 結構（K-06-quiz 會把 Q1/Q2 寫進 chapter_heading）
      // P2 應改成獨立 questions endpoint
      setQuestions(extractQuestionsFromScaffolds(sc));
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, [resourceId]);

  const handleAnswer = (qid: string, choice: string) => {
    if (revealed[qid]) return;
    setAnswers((prev) => ({ ...prev, [qid]: choice }));
    setRevealed((prev) => ({ ...prev, [qid]: true }));
  };

  // Group scaffolds by chapter（Q1 / Q2 / ...）
  const conceptByChapter = useMemo(() => {
    const map = new Map<string, ScaffoldEntry[]>();
    for (const s of scaffolds) {
      const ch = s.chapter_heading || '';
      if (!map.has(ch)) map.set(ch, []);
      map.get(ch)!.push(s);
    }
    return map;
  }, [scaffolds]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Link href="/login" className="text-emerald-600 hover:underline">請先登入 →</Link>
      </div>
    );
  }

  if (!resourceId) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center px-4">
        <h1 className="text-xl font-bold text-slate-800 mb-2">未指定考古題</h1>
        <Link href="/knowledge" className="mt-4 px-4 py-2 rounded-full bg-emerald-500 text-white">
          回學習庫
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        <Link
          href={subjectId ? `/knowledge?subjectId=${subjectId}` : '/knowledge'}
          className="flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> 學習庫
        </Link>
        <div className="text-sm font-medium text-slate-700 truncate flex-1">
          {filename}
        </div>
        <div className="text-xs text-slate-500">
          {Object.keys(revealed).length} / {questions.length} 已答
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-4 space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : questions.length === 0 ? (
          <div className="rounded-2xl bg-white border border-slate-200 p-6 text-center text-sm text-slate-500">
            此資源尚無解析出的題目（K-06-quiz prompt 須產出至少 1 題 + 對應 concept_extract）。
          </div>
        ) : (
          questions.map((q, idx) => {
            const userAns = answers[q.id];
            const showAnswer = revealed[q.id];
            const correct = userAns === q.correct_answer;
            const conceptScaffolds = conceptByChapter.get(`Q${idx + 1} ${q.content.slice(0, 30)}`) || [];

            return (
              <section
                key={q.id}
                className="rounded-2xl bg-white border border-slate-200 p-5"
                aria-label={`第 ${idx + 1} 題`}
              >
                <p className="text-sm font-bold text-slate-500 mb-1">第 {idx + 1} 題</p>
                <div className="text-base text-slate-900 mb-4">
                  <MathContent>{q.content}</MathContent>
                </div>

                <div className="space-y-2 mb-3">
                  {OPTION_KEYS.map((k) => {
                    const text = q[`option_${k.toLowerCase()}` as keyof QuizQuestion] as string | null;
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
                        <span className="flex items-start gap-2">
                          <span className="font-bold shrink-0">({k})</span>
                          <span className="flex-1"><MathContent>{text}</MathContent></span>
                          {showAnswer && isCorrectChoice && <Check className="shrink-0 w-4 h-4 text-emerald-600" />}
                          {showAnswer && isUserChoice && !isCorrectChoice && <X className="shrink-0 w-4 h-4 text-rose-600" />}
                        </span>
                      </button>
                    );
                  })}
                </div>

                {showAnswer && (
                  <>
                    <div className={`mt-2 text-sm ${correct ? 'text-emerald-700' : 'text-rose-700'} font-medium`}>
                      {correct ? '✓ 答對了！' : `✗ 正確答案：(${q.correct_answer})`}
                    </div>
                    {q.explanation && (
                      <div className="mt-2 text-xs text-slate-600 leading-relaxed">
                        <MathContent>{q.explanation}</MathContent>
                      </div>
                    )}
                    {/* concept_extract（K-06-quiz scaffold 寫成 takeaway 但 template_code='K-06-quiz')*/}
                    {conceptScaffolds
                      .filter((s) => s.type === 'takeaway')
                      .map((s) => (
                        <div
                          key={s.id}
                          className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3"
                        >
                          <p className="text-xs font-bold text-emerald-700 mb-1">📌 考點解析</p>
                          <div className="text-sm text-slate-800">
                            <MathContent>{s.content}</MathContent>
                          </div>
                        </div>
                      ))}
                    {/* pitfall（常見錯選陷阱）*/}
                    {conceptScaffolds
                      .filter((s) => s.type === 'pitfall')
                      .map((s) => (
                        <PitfallAlert
                          key={s.id}
                          scaffoldId={s.id}
                          chapterHeading={null}
                          content={s.content}
                        />
                      ))}
                  </>
                )}
              </section>
            );
          })
        )}
      </main>
    </div>
  );
}

/**
 * 從 K-06-quiz 解析 scaffolds 中重建題目結構。
 *
 * P1 簡化版：scaffolds 不含完整選項（K-06-quiz 把選項放在 questions[]）。
 * 此函式佔位：實作須 join /parsed 的 questions 與 scaffolds — 但目前
 * /parsed response 沒回 questions，須等 P2 endpoint 擴充。
 *
 * 暫回空陣列，UI 會顯示「尚無解析出的題目」空態（合理空，per QA Layer 3）。
 */
function extractQuestionsFromScaffolds(_scaffolds: ScaffoldEntry[]): QuizQuestion[] {
  return [];
}
