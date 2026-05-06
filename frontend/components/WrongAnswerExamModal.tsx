/**
 * @file WrongAnswerExamModal.tsx — 錯題考試挑題 Modal
 *
 * 流程：
 * 1. 用戶選題數（10/20/50/100）
 * 2. 呼叫 POST /wrong-answers/exam/pick
 * 3. 顯示 4 階段配比預覽（哪幾桶各幾題）
 * 4. 用戶確認後跳轉到 /exam/workspace 開考
 *    （題目透過 examService.create 包裝為臨時考試）
 */
'use client';

import { useState } from 'react';
import { X, Loader2, Target, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { reviewService, examService } from '@/lib/api/services';

const PHASE_META: Record<string, { label: string; emoji: string; color: string; desc: string }> = {
  final:    { label: 'Final 最後衝刺', emoji: '🚨', color: 'bg-red-50 text-red-700 border-red-200',         desc: '純鞏固已遇過題目' },
  sprint:   { label: 'Sprint 衝刺',    emoji: '⚡', color: 'bg-rose-50 text-rose-700 border-rose-200',     desc: '重複錯題鞏固為主' },
  standard: { label: 'Standard 穩紮',  emoji: '📚', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', desc: '探索與複習平衡' },
  mastery:  { label: 'Mastery 廣讀',   emoji: '🧭', color: 'bg-blue-50 text-blue-700 border-blue-200',     desc: '多新題曝光、廣度優先' },
};

const BUCKET_LABEL: Record<string, string> = {
  overdue: '🔴 過複習日',
  fresh:   '🟡 新錯題',
  weak:    '🟠 弱點節點',
  random:  '🟢 隨機補',
  overflow:'➕ 補足缺額',
};

interface Props {
  subjectId?: string;
  onClose: () => void;
}

const COUNT_OPTIONS = [10, 20, 50, 100];

interface PickResult {
  questions: { question_id: string }[];
  phase: 'final' | 'sprint' | 'standard' | 'mastery';
  phase_reason: string;
  buckets: Record<string, number>;
  total_candidates: number;
  message?: string;
}

export default function WrongAnswerExamModal({ subjectId, onClose }: Props) {
  const router = useRouter();
  const [count, setCount] = useState<number>(10);
  const [loading, setLoading] = useState(false);
  const [picked, setPicked] = useState<PickResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  async function handlePick() {
    setLoading(true);
    setError(null);
    try {
      const res = await reviewService.pickWrongAnswerExam({ subjectId, questionCount: count });
      setPicked(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : '挑題失敗');
    } finally {
      setLoading(false);
    }
  }

  async function handleStart() {
    if (!picked || picked.questions.length === 0) return;
    setStarting(true);
    try {
      // 直接用 picker 挑出的精確題目 ID 建立考試（status=READY，無需 AI 生成）
      const res = await examService.createFromQuestionIds(picked.questions.map(q => q.question_id));
      if (res.exam_id) {
        router.push(`/exam/workspace?examId=${res.exam_id}`);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : '建立考試失敗');
      setStarting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-3xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-emerald-500" />
            <h2 className="text-lg font-bold text-slate-900">錯題考試</h2>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full hover:bg-slate-100 text-slate-500">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Step 1: 選題數 */}
          <div>
            <p className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">選擇題數</p>
            <div className="grid grid-cols-4 gap-2">
              {COUNT_OPTIONS.map(n => (
                <button
                  key={n}
                  onClick={() => { setCount(n); setPicked(null); }}
                  className={`px-3 py-2 rounded-xl text-sm font-bold transition-colors border ${
                    count === n
                      ? 'bg-emerald-500 text-white border-emerald-500'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-emerald-300'
                  }`}
                >
                  {n} 題
                </button>
              ))}
            </div>
          </div>

          {/* Step 2: 預覽挑題 */}
          {!picked && (
            <button
              onClick={handlePick}
              disabled={loading}
              className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
              智能挑題預覽
            </button>
          )}

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700">
              {error}
            </div>
          )}

          {/* Step 3: 挑題結果 */}
          {picked && (
            <div className="space-y-3">
              {/* 階段標籤 */}
              <div className={`px-4 py-3 rounded-xl border ${PHASE_META[picked.phase]?.color || 'bg-slate-50 border-slate-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xl">{PHASE_META[picked.phase]?.emoji}</span>
                  <span className="font-bold text-sm">{PHASE_META[picked.phase]?.label}</span>
                </div>
                <p className="text-xs italic">{picked.phase_reason}</p>
                <p className="text-[11px] text-slate-600 mt-1">{PHASE_META[picked.phase]?.desc}</p>
              </div>

              {/* 配比明細 */}
              {picked.questions.length > 0 ? (
                <>
                  <div className="bg-slate-50 rounded-xl p-3">
                    <p className="text-xs font-bold text-slate-700 mb-2">挑題配比（共 {picked.questions.length} 題 / 候選池 {picked.total_candidates}）</p>
                    <div className="space-y-1">
                      {Object.entries(picked.buckets)
                        .filter(([, n]) => n > 0)
                        .map(([k, n]) => (
                          <div key={k} className="flex items-center justify-between text-xs">
                            <span className="text-slate-700">{BUCKET_LABEL[k] || k}</span>
                            <span className="font-bold text-slate-900">{n} 題</span>
                          </div>
                        ))}
                    </div>
                  </div>
                  <button
                    onClick={handleStart}
                    disabled={starting}
                    className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-3 rounded-xl font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {starting ? <Loader2 className="h-5 w-5 animate-spin" /> : <Target className="h-5 w-5" />}
                    開始考試（{picked.questions.length} 題）
                  </button>
                </>
              ) : (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
                  <p className="text-sm text-amber-800 font-medium">
                    {picked.message || '目前無錯題可考'}
                  </p>
                  <p className="text-xs text-amber-700 mt-1">去 /practice 練習或完成測驗累積錯題後再試</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
